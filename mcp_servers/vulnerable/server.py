"""Vulnerable reference MCP server.

Implements the prompt's §"Vulnerable MCP Server":

- Shared in-process transport (deliberate).
- Dynamic tool registration (schema confusion possible).
- File-resource resolver that **follows symlinks** (deliberate).
- No auth on ``list_tools``.
- Cache layer keyed on ``(tenant_id, tool_name)`` only.

Each hole is toggled by a ``VulnFlags`` env-flag so reviewers can
flip a single hole on/off at runtime.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


def _env_flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.lower() in ("1", "true", "yes", "on")


@dataclass
class VulnFlags:
    """Toggleable vulnerability flags. Defaults match the prompt's §server."""

    dynamic_tools: bool = field(default_factory=lambda: _env_flag("VULN_DYNAMIC_TOOLS", True))
    follow_symlinks: bool = field(default_factory=lambda: _env_flag("VULN_FOLLOW_SYMLINKS", True))
    no_auth_list: bool = field(default_factory=lambda: _env_flag("VULN_NO_AUTH_LIST", True))
    shared_cache_key: bool = field(default_factory=lambda: _env_flag("VULN_SHARED_CACHE_KEY", True))
    shared_transport: bool = field(default_factory=lambda: _env_flag("VULN_SHARED_TRANSPORT", True))


@dataclass
class _Worker:
    """Single shared worker used by every tenant (deliberate violation)."""

    tools: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = field(default_factory=dict)
    cache: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)
    fixtures_root: Path | None = None

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        handler = self.tools.get(name)
        if handler is None:
            return {"error": {"code": -32601, "message": f"tool {name!r} not found"}}
        return {"result": handler(arguments)}


class VulnerableServer:
    """In-process vulnerable MCP server."""

    def __init__(self, flags: VulnFlags | None = None) -> None:
        self.flags = flags or VulnFlags()
        # Deliberate: one shared worker regardless of tenant.
        self._worker = _Worker()
        self._register_default_tools()
        logger.info("VulnerableServer flags=%s", self.flags)

    # ---------- tool registry ----------

    def _register_default_tools(self) -> None:
        self._worker.tools["echo"] = lambda args: {"echo": args}
        self._worker.tools["scratchpad_write"] = self._scratchpad_write
        self._worker.tools["scratchpad_read"] = self._scratchpad_read
        self._worker.tools["set_env"] = self._set_env
        self._worker.tools["cache_lookup"] = self._cache_lookup
        self._worker.tools["fetch_url"] = self._fetch_url

    def register_tool(
        self, name: str, handler: Callable[[dict[str, Any]], dict[str, Any]]
    ) -> None:
        """Dynamic tool registration (deliberate; allows schema confusion)."""
        if not self.flags.dynamic_tools:
            raise PermissionError("VULN_DYNAMIC_TOOLS is disabled")
        self._worker.tools[name] = handler
        logger.warning("dynamically registered tool %r (vuln flag enabled)", name)

    def list_tools(self) -> list[dict[str, Any]]:
        # Deliberate: no auth check.
        return [
            {"name": n, "description": f"vulnerable tool {n}"} for n in self._worker.tools
        ]

    # ---------- resource resolver ----------

    def set_fixtures_root(self, root: Path) -> None:
        self._worker.fixtures_root = root

    def read_resource(self, uri: str) -> dict[str, Any]:
        """Resolve ``uri`` against the fixtures root.

        Deliberately follows symlinks when ``VULN_FOLLOW_SYMLINKS`` is on.
        """
        if self._worker.fixtures_root is None:
            return {"error": {"code": -32602, "message": "no fixtures root"}}
        if not uri.startswith("file:///"):
            return {"error": {"code": -32602, "message": "unsupported scheme"}}
        rel = uri[len("file:///") :]
        # Strip any leading tenant dir to avoid double-prefixing.
        for tenant in ("tenant-A", "tenant-B"):
            if rel.startswith(f"{tenant}/"):
                rel = rel[len(tenant) + 1 :]
                break
        target = (self._worker.fixtures_root / rel).resolve()
        if not self.flags.follow_symlinks and target.is_symlink():
            return {"error": {"code": -32603, "message": "symlink denied"}}
        if not target.exists():
            return {"error": {"code": -32604, "message": "not found"}}
        return {"result": {"uri": uri, "contents": [{"uri": uri, "text": target.read_text()}]}}

    # ---------- handlers ----------

    def _scratchpad_write(self, args: dict[str, Any]) -> dict[str, Any]:
        key = args.get("key", "")
        value = args.get("value", "")
        # Deliberate: no tenant scope on scratchpad.
        self._worker.cache[("scratchpad", key)] = {"value": value}
        return {"ok": True}

    def _scratchpad_read(self, args: dict[str, Any]) -> dict[str, Any]:
        key = args.get("key", "")
        return self._worker.cache.get(("scratchpad", key), {"value": None})

    def _set_env(self, args: dict[str, Any]) -> dict[str, Any]:
        # Deliberate: tenant-agnostic env-var overwrite.
        os.environ[args.get("name", "")] = args.get("value", "")
        return {"ok": True}

    def _cache_lookup(self, args: dict[str, Any]) -> dict[str, Any]:
        tool = args.get("tool", "")
        q = args.get("q", "")
        if self.flags.shared_cache_key:
            # Deliberate: cache key omits prompt_hash.
            key = ("cache", tool)
        else:
            key = ("cache", tool, q)
        if key in self._worker.cache:
            return self._worker.cache[key]
        value = {"echo": args}
        self._worker.cache[key] = value
        return value

    def _fetch_url(self, args: dict[str, Any]) -> dict[str, Any]:
        # Deliberate: SSRF + token forwarding.
        url = args.get("url", "")
        return {"result": {"fetched": url, "forwarded_auth": bool(args.get("forward_auth"))}}

    # ---------- shared transport ----------

    def call_tool_as(self, tenant_id: str, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call ``name`` while impersonating ``tenant_id``.

        Deliberately ignores ``tenant_id`` when
        ``VULN_SHARED_TRANSPORT`` is on (default).
        """
        if not self.flags.shared_transport:
            # In a fixed version this would route to a per-tenant worker.
            pass
        return self._worker.call_tool(name, arguments)


def build_server(*args: Any, **kwargs: Any) -> VulnerableServer:
    """Construct and return the vulnerable MCP server."""
    return VulnerableServer(*args, **kwargs)


__all__ = ["VulnFlags", "VulnerableServer", "build_server"]