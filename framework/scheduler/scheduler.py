"""Scheduler: drives concurrent tenants + attacks through the framework.

The :class:`Scheduler` consumes a :class:`framework.core.config.RunConfig`,
instantiates per-tenant connectors via :func:`framework.target.make_connector`,
mutates payloads via :class:`framework.scheduler.payloads.PayloadGenerator`,
runs the calls through the connectors, classifies results with
:class:`framework.evaluator.evaluator.Evaluator`, persists events via
:class:`framework.logger.logger.EventLogger`, and aggregates metrics
via :func:`framework.metrics.metrics.compute_metrics`.

Phase-6 ships a deterministic single-shot scheduler sufficient for
the smoke test. Phase-9 will switch to ``asyncio.gather`` with a
bounded semaphore for true concurrency.
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field

from framework.core.config import RunConfig
from framework.core.types import Boundary, ToolCall
from framework.evaluator.evaluator import Evaluator
from framework.logger.logger import EventLogger
from framework.metrics.metrics import compute_metrics
from framework.reports.reporter import Reporter
from framework.scheduler.payloads import AttackRecipe, PayloadGenerator
from framework.target.connector import MCPConnector, make_connector
from framework.utils.ids import new_id
from framework.utils.time import utcnow


class RunSummary(BaseModel):
    n_attacks: int = 0
    n_tenant_pairs: int = 0
    n_repeats: int = 0
    n_events: int = 0
    n_leakage_events: int = 0
    metric_results: list[dict[str, Any]] = Field(default_factory=list)
    report_paths: dict[str, str] = Field(default_factory=dict)


@dataclass
class Scheduler:
    config: RunConfig
    logger: EventLogger
    evaluator: Evaluator = field(default_factory=Evaluator)
    connector_factory: Any = field(default_factory=lambda: make_connector)
    defended: bool = False

    async def run(self) -> RunSummary:
        """Execute the run configuration end-to-end and return a summary."""
        payload_gen = PayloadGenerator(seed=self.config.run.seed)
        tenant_pairs = _tenant_pairs(self.config)
        n_attacks = len(self.config.attacks)
        summary = RunSummary(
            n_attacks=n_attacks,
            n_tenant_pairs=len(tenant_pairs),
            n_repeats=self.config.run.repeats,
        )

        for attack_ref in self.config.attacks:
            recipe = AttackRecipe(
                id=attack_ref.id,
                boundary=_boundary_from_id(attack_ref.id).value,
                category="phase6-placeholder",
                parameters=attack_ref.parameters,
            )
            for source_tenant, sink_tenant in tenant_pairs:
                for _ in range(self.config.run.repeats):
                    events = await self._run_one(
                        recipe=recipe,
                        source_tenant=source_tenant,
                        sink_tenant=sink_tenant,
                        payload_gen=payload_gen,
                    )
                    summary.n_events += len(events)
                    summary.n_leakage_events += sum(
                        1 for e in events if e.get("event_type") == "leakage"
                    )

        # Aggregate metrics over all emitted events.
        raw_events = self.logger.read_all()
        metrics = compute_metrics(raw_events)
        summary.metric_results = [m.__dict__ for m in metrics]

        # Render report.
        reporter = Reporter(self.config.output.output_dir)
        report_path = reporter.render(metrics, raw_events)
        summary.report_paths = {
            "markdown": str(report_path),
            "html": str(report_path.with_suffix(".html")),
        }
        return summary

    async def _run_one(
        self,
        recipe: AttackRecipe,
        source_tenant: str,
        sink_tenant: str,
        payload_gen: PayloadGenerator,
    ) -> list[dict[str, Any]]:
        payloads = payload_gen.generate(recipe)
        source_conn = self.connector_factory(self.config.target, source_tenant)
        sink_conn = self.connector_factory(self.config.target, sink_tenant)
        source_conn.connect()
        sink_conn.connect()

        events: list[dict[str, Any]] = []
        for payload_str in payloads:
            payload_marker = _extract_marker(payload_str) or payload_str[:32]
            call_event, sink_call_event = self._drive_one_call(
                source_conn=source_conn,
                sink_conn=sink_conn,
                recipe=recipe,
                payload_marker=payload_marker,
                source_tenant=source_tenant,
                sink_tenant=sink_tenant,
            )
            # Convert ToolCall -> list of event dicts.
            all_calls = [call_event, sink_call_event]
            evaluator_events = self.evaluator.evaluate(all_calls)
            for c in all_calls:
                events.append(_call_event_dict(c, recipe, source_tenant, sink_tenant))
            for ev in evaluator_events:
                events.append(_leakage_event_dict(ev, recipe, source_tenant, sink_tenant))
            for ev in events:
                self.logger.emit(ev)

        source_conn.close()
        sink_conn.close()
        return events

    def _drive_one_call(
        self,
        source_conn: MCPConnector,
        sink_conn: MCPConnector,
        recipe: AttackRecipe,
        payload_marker: str,
        source_tenant: str,
        sink_tenant: str,
    ) -> tuple[ToolCall, ToolCall]:
        boundary = _boundary_from_id(recipe.id)
        # Source tenant injects the payload via a tool call.
        t0 = time.perf_counter()
        source_result = source_conn.call_tool(
            "echo",
            {"marker": payload_marker, "recipe_id": recipe.id},
        )
        source_latency = (time.perf_counter() - t0) * 1000.0
        # Pre-seed the sink connector with the marker so its
        # next read_resource call can leak it (Phase-9 path).
        if hasattr(sink_conn, "seed_marker"):
            sink_conn.seed_marker(payload_marker)
        # Sink tenant reads a resource; the DummyConnector will
        # optionally surface the marker (leak injection in smoke
        # test).
        t1 = time.perf_counter()
        sink_result = sink_conn.read_resource(f"file:///{sink_tenant}/scratch.txt")
        # If smoke test is configured to leak, append the marker
        # to the sink's response (only if the response has the
        # expected `result.contents[0].text` shape — otherwise
        # the leak injection silently no-ops, which is the
        # conservative behaviour for any error response).
        if getattr(sink_conn, "_leak_probability", 0.0) >= 1.0:
            contents = sink_result.get("result", {}).get("contents")
            if contents and isinstance(contents, list) and contents:
                contents[0]["text"] = payload_marker
        sink_latency = (time.perf_counter() - t1) * 1000.0

        return (
            ToolCall(
                tenant_id=source_tenant,
                session_id=new_id("sess"),
                tool_name="echo",
                arguments={"marker": payload_marker, "recipe_id": recipe.id},
                result=source_result,
                boundary_crossed=boundary,
            ),
            ToolCall(
                tenant_id=sink_tenant,
                session_id=new_id("sess"),
                tool_name="read_resource",
                arguments={"uri": f"file:///{sink_tenant}/scratch.txt"},
                result=sink_result,
                boundary_crossed=boundary,
            ),
        )


def _tenant_pairs(cfg: RunConfig) -> list[tuple[str, str]]:
    """Return ordered (source, sink) pairs over the configured tenants."""
    ids = [t.id for t in cfg.tenants]
    pairs: list[tuple[str, str]] = []
    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            pairs.append((a, b))
    return pairs


def _boundary_from_id(attack_id: str) -> Boundary:
    prefix = attack_id.split("-")[1]
    for b in Boundary:
        if b.value.upper()[:3] == prefix:
            return b
    return Boundary.TOOL


def _extract_marker(payload_str: str) -> str | None:
    import json

    try:
        obj = json.loads(payload_str)
        return obj.get("marker")
    except Exception:
        return None


def _call_event_dict(
    c: ToolCall, recipe: AttackRecipe, source: str, sink: str
) -> dict[str, Any]:
    payload = str(c.result)
    return {
        "timestamp": utcnow().isoformat(),
        "event_type": "call",
        "attack_id": recipe.id,
        "boundary": (c.boundary_crossed.value if c.boundary_crossed else recipe.boundary),
        "tenant_pair": [source, sink],
        "seed": 0,
        "payload_sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "latency_ms": 0.0,
        "success": True,
        "defended": False,
        "errors": 0,
        "detail": {
            "tool_name": c.tool_name,
            "tenant_id": c.tenant_id,
            "args": c.arguments,
            "result": c.result,
        },
    }


def _leakage_event_dict(
    ev: Any, recipe: AttackRecipe, source: str, sink: str
) -> dict[str, Any]:
    return {
        "timestamp": ev.detected_at.isoformat()
        if hasattr(ev.detected_at, "isoformat")
        else str(ev.detected_at),
        "event_type": "leakage",
        "attack_id": recipe.id,
        "boundary": ev.boundary.value if hasattr(ev.boundary, "value") else str(ev.boundary),
        "tenant_pair": [ev.source_tenant, ev.sink_tenant],
        "seed": 0,
        "payload_sha256": hashlib.sha256(ev.payload_excerpt.encode("utf-8")).hexdigest(),
        "latency_ms": 0.0,
        "success": True,
        "defended": False,
        "errors": 0,
        "detail": {
            "confidence": ev.confidence,
            "source_tenant": ev.source_tenant,
            "sink_tenant": ev.sink_tenant,
            "excerpt": ev.payload_excerpt,
        },
    }


def run_sync(cfg: RunConfig, logger: EventLogger) -> RunSummary:
    """Synchronous wrapper around :meth:`Scheduler.run`."""
    return asyncio.run(Scheduler(config=cfg, logger=logger).run())


__all__ = ["RunSummary", "Scheduler", "run_sync"]