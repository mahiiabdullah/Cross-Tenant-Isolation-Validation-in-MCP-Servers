"""Metric computations.

Aggregates raw events emitted by :class:`framework.evaluator.Evaluator`
into per-(attack_id, boundary) statistical summaries.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass
class MetricResult:
    leakage_rate: float
    time_to_leak_ms: float | None
    defense_overhead_ms: float | None
    utility_retention: float | None
    n_events: int = 0
    attack_id: str = ""
    boundary: str = ""


def compute_metrics(events: Iterable[dict[str, Any]]) -> list[MetricResult]:
    """Aggregate raw event dicts into MetricResults.

    ``events`` is an iterable of dicts with keys:
    ``attack_id``, ``boundary``, ``success`` (bool), ``latency_ms``
    (float|None), ``event_type`` (``"leakage" | "call" | ...``),
    ``defended`` (bool|None), ``errors`` (int|None).
    """
    events = list(events)
    by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for e in events:
        key = (e.get("attack_id", ""), e.get("boundary", ""))
        by_key.setdefault(key, []).append(e)

    results: list[MetricResult] = []
    for (attack_id, boundary), group in by_key.items():
        leak_events = [e for e in group if e.get("event_type") == "leakage"]
        call_events = [e for e in group if e.get("event_type") == "call"]
        n_total = len(call_events) or len(group) or 1
        leakage_rate = len(leak_events) / n_total

        # Time-to-leak: median latency of leakage events that
        # carry a latency_ms field.
        leak_latencies = [
            float(e["latency_ms"])
            for e in leak_events
            if e.get("latency_ms") is not None
        ]
        ttl = statistics.median(leak_latencies) if leak_latencies else None

        # Defence overhead: difference of p95 latencies.
        defended = [e for e in group if e.get("defended") is True]
        undefended = [e for e in group if e.get("defended") is False]
        overhead = _p95_diff(defended, undefended)

        # Utility retention: 1 - (errors_with / errors_without).
        utility = _utility_retention(defended, undefended)

        results.append(
            MetricResult(
                leakage_rate=leakage_rate,
                time_to_leak_ms=ttl,
                defense_overhead_ms=overhead,
                utility_retention=utility,
                n_events=len(group),
                attack_id=attack_id,
                boundary=boundary,
            )
        )
    return results


def _p95(diff_group: list[dict[str, Any]], base_group: list[dict[str, Any]]) -> float | None:
    def p95(g: list[dict[str, Any]]) -> float | None:
        vals = sorted(float(e["latency_ms"]) for e in g if e.get("latency_ms") is not None)
        if not vals:
            return None
        idx = max(0, int(round(0.95 * (len(vals) - 1))))
        return vals[idx]

    a, b = p95(diff_group), p95(base_group)
    if a is None or b is None:
        return None
    return a - b


def _p95_diff(a: list[dict[str, Any]], b: list[dict[str, Any]]) -> float | None:
    return _p95(a, b)


def _utility_retention(
    defended: list[dict[str, Any]], undefended: list[dict[str, Any]]
) -> float | None:
    err_def = sum(int(e.get("errors", 0) or 0) for e in defended)
    err_un = sum(int(e.get("errors", 0) or 0) for e in undefended)
    if err_un == 0:
        return 1.0 if err_def == 0 else 0.0
    ratio = err_def / err_un
    return max(0.0, min(1.0, 1.0 - ratio))


__all__ = ["MetricResult", "compute_metrics"]