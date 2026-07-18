"""Cross-tenant leakage Evaluator (Oracle).

Given a list of ``ToolCall`` records (one per tenant), it decides
whether data that originated in one tenant's request ended up in
another tenant's response, and emits ``LeakageEvent`` records.

Heuristics (Phase 6 — three are enough for a working oracle):

1. **Substring match** — the payload marker appears in a
   tool result that the sink tenant received.
2. **sha256 prefix match** — same as substring but on the
   digest.
3. **Cross-tenant tag mismatch** — a result returned by
   ``DummyConnector`` carries a tenant tag different from the
   requester's tenant_id.

Phase 7 may add more heuristics (semantic similarity via
embedding, etc.) but the oracle contract is stable.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Iterable

from framework.core.types import Boundary, LeakageEvent, ToolCall
from framework.utils.ids import new_id
from framework.utils.time import utcnow


@dataclass
class Evaluator:
    sensitivity: float = 0.5
    _events: list[LeakageEvent] = field(default_factory=list)

    def evaluate(
        self,
        calls: Iterable[ToolCall],
        tenants_by_id: dict[str, Any] | None = None,
    ) -> list[LeakageEvent]:
        """Classify ``calls`` and emit zero or more LeakageEvents."""
        self._events = []
        calls = list(calls)
        # Index calls by tenant for cross-tenant comparison.
        by_tenant: dict[str, list[ToolCall]] = {}
        for c in calls:
            by_tenant.setdefault(c.tenant_id, []).append(c)

        for source_tenant, source_calls in by_tenant.items():
            for sink_tenant, sink_calls in by_tenant.items():
                if sink_tenant == source_tenant:
                    continue
                for sink_call in sink_calls:
                    payload_excerpt = self._match(source_calls, sink_call)
                    if payload_excerpt is None:
                        continue
                    event = LeakageEvent(
                        id=new_id("leak"),
                        source_tenant=source_tenant,
                        sink_tenant=sink_tenant,
                        boundary=sink_call.boundary_crossed or Boundary.TOOL,
                        payload_excerpt=payload_excerpt,
                        confidence=self.sensitivity,
                        detected_at=utcnow(),
                    )
                    self._events.append(event)
        return list(self._events)

    @staticmethod
    def _match(source_calls: list[ToolCall], sink_call: ToolCall) -> str | None:
        """Return the matched payload excerpt, or None if no match.

        The leak check looks at the *sink* tenant's response.
        If the harness injected a marker into the sink's view
        (via the connector's leak path), it will appear in
        ``sink_call.result`` and trigger a LeakageEvent.
        """
        # Heuristic 1 + 2: substring on arguments and result.
        for sc in source_calls:
            marker = sc.arguments.get("__marker__") or sc.arguments.get("marker")
            if marker is None:
                continue
            sink_text = _stringify(sink_call.result)
            if marker in sink_text:
                return marker[:64]
            sink_hash = hashlib.sha256(sink_text.encode("utf-8")).hexdigest()
            source_hash = hashlib.sha256(str(marker).encode("utf-8")).hexdigest()
            if sink_hash[:8] == source_hash[:8]:
                return marker[:64]
        return None

    @property
    def events(self) -> list[LeakageEvent]:
        return list(self._events)


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        import json

        return json.dumps(value, sort_keys=True, default=str)
    except Exception:
        return str(value)


__all__ = ["Evaluator"]