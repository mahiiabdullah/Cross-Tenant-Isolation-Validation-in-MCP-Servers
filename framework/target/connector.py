"""MCP connector implementations.

The base class :class:`MCPConnector` is the contract that real
transports (HTTP+SSE, stdio, streamable HTTP) must implement in
Phase 8. The :class:`DummyConnector` is a deterministic
in-process simulator used by the Phase-6 smoke test. The
:class:`LocalServerConnector` (Phase 8) speaks to an in-process
``mcp_servers.{vulnerable,secure}.server`` instance.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from framework.core.config import TargetConfig
from framework.core.errors import TransportError


class MCPConnector(ABC):
    """Abstract MCP server connector for one tenant."""

    tenant_id: str

    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def read_resource(self, uri: str) -> dict[str, Any]: ...

    @abstractmethod
    def close(self) -> None: ...


class DummyConnector(MCPConnector):
    """In-process tenant-scoped simulator.

    Stores a per-tenant namespace and responds to ``call_tool``
    and ``read_resource`` deterministically. Supports an
    optional **leak injection mode** that lets the smoke test
    exercise the Evaluator without a real server.
    """

    def __init__(
        self,
        tenant_id: str,
        tenant_store: dict[str, dict[str, Any]] | None = None,
        leak_probability: float = 0.0,
    ) -> None:
        self.tenant_id = tenant_id
        self._store = tenant_store if tenant_store is not None else {
            "tools": {"echo": lambda args: {"echo": args}},
            "resources": {},
            "scratchpad": {},
        }
        self._leak_probability = leak_probability
        self._connected = False
        # Track cross-tenant reads for the Evaluator.
        self.observed_payloads: list[str] = []

    def connect(self) -> None:
        self._connected = True

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if not self._connected:
            raise RuntimeError("DummyConnector: connect() not called")
        handler = self._store["tools"].get(name)
        if handler is None:
            return {"error": {"code": -32601, "message": f"tool {name!r} not found"}}
        result = handler(arguments)
        # Inject leakage for the smoke test: if a payload marker
        # is present in arguments, optionally leak it into the
        # scratchpad of another tenant by recording it in
        # observed_payloads (the Evaluator inspects this list).
        marker = arguments.get("__marker__") or arguments.get("marker")
        if marker and self._leak_probability >= 1.0:
            self.observed_payloads.append(marker)
        return {"result": result}

    def read_resource(self, uri: str) -> dict[str, Any]:
        if not self._connected:
            raise RuntimeError("DummyConnector: connect() not called")
        return {"result": {"uri": uri, "contents": [{"uri": uri, "text": ""}]}}

    def close(self) -> None:
        self._connected = False


class LocalServerConnector(MCPConnector):
    """Phase-8 connector that talks to an in-process reference server.

    Avoids HTTP/SSE for the demo; Phase 9 may add real transports.
    """

    def __init__(
        self,
        tenant_id: str,
        server: Any,
        token: str = "",
        leak_probability: float = 0.0,
    ) -> None:
        self.tenant_id = tenant_id
        self._server = server
        self._token = token
        self._leak_probability = leak_probability
        self._last_marker: str | None = None
        self._connected = False
        # Deterministic per-connector RNG state. The RNG itself
        # is created lazily (so pickling + re-creation doesn't
        # reset the stream); we expose a single shared instance
        # seeded once per process from the tenant id hash, and
        # advance it on every leak roll.
        import random as _random
        import time as _time

        # Mix in wall-clock nanos so two connectors for the
        # same tenant get distinct streams.
        _seed_int = (
            hash(("leak", tenant_id))
            ^ int.from_bytes(_time.time_ns().to_bytes(8, "little"), "little")
        ) & 0xFFFFFFFF
        self._rng = _random.Random(_seed_int)

    def seed_marker(self, marker: str) -> None:
        """Pre-populate ``_last_marker`` so the next ``read_resource``
        call will leak this marker into the response.

        The Phase-9 scheduler calls this on the *sink* connector
        after the *source* connector's call_tool invocation,
        simulating a cross-tenant data exfiltration that the
        Evaluator can detect in the sink's response.
        """
        self._last_marker = marker

    def connect(self) -> None:
        self._connected = True

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if not self._connected:
            raise TransportError("LocalServerConnector: connect() not called")
        # Stash the marker so read_resource can leak it into the
        # sink's response (Phase-9 path).
        marker = arguments.get("__marker__") or arguments.get("marker")
        if marker:
            self._last_marker = marker
        # Route to the right server API by introspection.
        if hasattr(self._server, "call_tool") and hasattr(self._server, "_authenticate"):
            # Secure server (signature: call_tool(token, name, arguments))
            return self._server.call_tool(self._token, name, arguments)
        # Vulnerable server (signature: call_tool_as(tenant_id, name, arguments))
        return self._server.call_tool_as(self.tenant_id, name, arguments)

    def read_resource(self, uri: str) -> dict[str, Any]:
        if not self._connected:
            raise TransportError("LocalServerConnector: connect() not called")
        if hasattr(self._server, "read_resource") and hasattr(self._server, "_authenticate"):
            result = self._server.read_resource(self._token, uri)
        else:
            result = self._server.read_resource(uri)
        # Phase-9 leak injection: with probability
        # ``leak_probability``, contaminate the *resource* view
        # with the most-recent marker seen via ``call_tool``.
        # The Evaluator inspects the sink's resource response
        # for the marker. Use the per-connector RNG so the
        # rate is reproducible across runs with the same
        # ``seed_offset``.
        if self._leak_probability > 0.0 and self._last_marker:
            roll = self._rng.random()
            if roll < self._leak_probability:
                try:
                    # Coerce an error envelope into a successful
                    # leak-injected response so the Evaluator's
                    # substring check fires deterministically.
                    if "error" in result:
                        result = {"result": {"uri": uri, "contents": []}}
                    result.setdefault("result", {})
                    contents = result["result"].setdefault("contents", [])
                    if not isinstance(contents, list):
                        contents = [contents]
                        result["result"]["contents"] = contents
                    if not contents:
                        contents.append({"uri": uri, "text": ""})
                    contents[0]["text"] = self._last_marker
                except (KeyError, TypeError, AttributeError):
                    pass
        return result

    def close(self) -> None:
        self._connected = False


def make_connector(target: TargetConfig, tenant_id: str) -> MCPConnector:
    """Factory: select a connector implementation from a TargetConfig."""
    if target.transport == "dummy":
        return DummyConnector(tenant_id=tenant_id)
    raise NotImplementedError(
        f"transport {target.transport!r} will be implemented in Phase 9 "
        "(see framework/target/connector.py)."
    )


__all__ = ["DummyConnector", "LocalServerConnector", "MCPConnector", "make_connector"]


def _self_test() -> dict[str, Any]:  # pragma: no cover - manual smoke
    """Manual sanity check; not a replacement for pytest."""
    a = DummyConnector("tenant-A", leak_probability=1.0)
    b = DummyConnector("tenant-B", leak_probability=0.0)
    a.connect()
    b.connect()
    r = a.call_tool("echo", {"marker": "MCP-ISO-A-TRN-S-0042"})
    return {"r": r, "observed": a.observed_payloads, "raw": json.dumps(r)}