"""Shared utilities used by concrete attack classes."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from pydantic import BaseModel, Field

from framework.target.connector import MCPConnector


class AttackContext(BaseModel):
    """Per-attack invocation context.

    Phase 7 uses this to thread the source and sink connectors,
    the payload marker, the seed, and any recipe parameters
    through to the attack's ``execute()`` method.
    """

    source_connector: Any = Field(exclude=True)
    sink_connector: Any = Field(exclude=True)
    payload_marker: str
    seed: int = 0
    parameters: dict[str, Any] = Field(default_factory=dict)


def marker_match(payload_marker: str, observed: Any) -> bool:
    """Return True if the payload marker matches the observed value.

    Two heuristics, mirroring the Phase-6 Evaluator:

    1. Substring match against the stringified observation.
    2. sha256-prefix match against the stringified observation.
    """
    text = _stringify(observed)
    if payload_marker in text:
        return True
    h_obs = hashlib.sha256(text.encode("utf-8")).hexdigest()
    h_src = hashlib.sha256(payload_marker.encode("utf-8")).hexdigest()
    return h_obs[:8] == h_src[:8]


def dispatch_call(connector: MCPConnector, name: str, args: dict[str, Any]) -> tuple[dict[str, Any], float]:
    """Call a tool on ``connector`` and return (response, latency_ms)."""
    t0 = time.perf_counter()
    response = connector.call_tool(name, args)
    return response, (time.perf_counter() - t0) * 1000.0


def dispatch_read(connector: MCPConnector, uri: str) -> tuple[dict[str, Any], float]:
    t0 = time.perf_counter()
    response = connector.read_resource(uri)
    return response, (time.perf_counter() - t0) * 1000.0


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    import json

    try:
        return json.dumps(value, sort_keys=True, default=str)
    except Exception:
        return str(value)


__all__ = [
    "AttackContext",
    "dispatch_call",
    "dispatch_read",
    "marker_match",
]
