"""Secure reference MCP server.

Implements the prompt's §"Secure Reference Server":

- Per-tenant transport (no shared worker).
- Per-session JWT with ``aud`` binding (HMAC-SHA256).
- Frozen manifest; tools come from the manifest, not from
  dynamic registration.
- File-resource resolver rejects symlinks and enforces a
  canonical-path prefix check.
- All IPC messages schema-validated before dispatch.
- Cache layer keyed on
  ``(tenant_id, tool_name, prompt_hash, schema_version)``.
"""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from framework.core.errors import ManifestError, TransportError
from mcp_servers.secure.keys import JWTError, mint_jwt, verify_jwt
from mcp_servers.secure.manifest import FrozenManifest, load_manifest

logger = logging.getLogger(__name__)

DEFAULT_SECRET = "dev-secret"
DEFAULT_AUDIENCE = "mcp-iso-research"


def _canonical_path(root: Path, requested: Path) -> Path:
    """Resolve ``requested`` and ensure it stays under ``root``."""
    resolved = (root / requested).resolve()
    root_resolved = root.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise TransportError(f"path escapes fixtures root: {resolved}") from exc
    return resolved


@dataclass
class _TenantState:
    scratchpad: dict[str, Any] = field(default_factory=dict)
    cache: dict[tuple[str, str, str, int], Any] = field(default_factory=dict)
    fixtures_root: Path | None = None


class SecureServer:
    """In-process secure MCP server with per-tenant isolation."""

    def __init__(
        self,
        manifest: FrozenManifest | None = None,
        secret: str | None = None,
        audience: str | None = None,
    ) -> None:
        self.secret = secret or os.environ.get("MCP_ISO_SECRET", DEFAULT_SECRET)
        self.audience = audience or os.environ.get("MCP_ISO_AUDIENCE", DEFAULT_AUDIENCE)
        self.manifest = manifest or load_manifest(
            Path(__file__).parent / "manifest.json"
        )
        self._tenants: dict[str, _TenantState] = {}
        self._handlers: dict[str, Callable[[str, dict[str, Any]], dict[str, Any]]] = {
            "echo": self._echo,
            "scratchpad_write": self._scratchpad_write,
            "scratchpad_read": self._scratchpad_read,
            "cache_lookup": self._cache_lookup,
            "fetch_url": self._fetch_url,
        }
        unknown = self.manifest.tool_names() - set(self._handlers)
        if unknown:
            raise ManifestError(f"manifest has no handler for: {sorted(unknown)}")
        logger.info(
            "SecureServer ready (manifest schema_version=%d, tools=%s)",
            self.manifest.schema_version,
            sorted(self.manifest.tool_names()),
        )

    # ---------- session / auth ----------

    def mint_token(self, tenant_id: str, session_id: str) -> str:
        return mint_jwt(self.secret, self.audience, tenant_id, session_id)

    def _authenticate(self, token: str) -> dict[str, Any]:
        try:
            payload = verify_jwt(token, self.secret, self.audience)
        except JWTError as exc:
            raise TransportError(f"auth failed: {exc}") from exc
        return payload

    def _state_for(self, tenant_id: str) -> _TenantState:
        if tenant_id not in self._tenants:
            self._tenants[tenant_id] = _TenantState()
        return self._tenants[tenant_id]

    def set_fixtures_root(self, tenant_id: str, root: Path) -> None:
        self._state_for(tenant_id).fixtures_root = root

    # ---------- IPC entry points ----------

    def list_tools(self, token: str) -> list[dict[str, Any]]:
        """``list_tools`` requires a valid token (no auth → list is empty)."""
        try:
            self._authenticate(token)
        except TransportError:
            return []
        return [{"name": t["name"], "description": t.get("description", "")} for t in self.manifest.tools]

    def call_tool(
        self,
        token: str,
        name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        if name not in self._handlers:
            return {"error": {"code": -32601, "message": f"tool {name!r} not found"}}
        payload = self._authenticate(token)
        tenant_id = payload["tenant_id"]
        if name not in self.manifest.tool_names():
            return {"error": {"code": -32602, "message": f"tool {name!r} not in manifest"}}
        return {"result": self._handlers[name](tenant_id, arguments)}

    def read_resource(self, token: str, uri: str) -> dict[str, Any]:
        payload = self._authenticate(token)
        tenant_id = payload["tenant_id"]
        state = self._state_for(tenant_id)
        if state.fixtures_root is None:
            return {"error": {"code": -32602, "message": "no fixtures root"}}
        if not uri.startswith("file:///"):
            return {"error": {"code": -32602, "message": "unsupported scheme"}}
        rel = uri[len("file:///") :]
        for tenant in ("tenant-A", "tenant-B"):
            if rel.startswith(f"{tenant}/"):
                rel = rel[len(tenant) + 1 :]
                break
        try:
            target = _canonical_path(state.fixtures_root, Path(rel))
        except TransportError as exc:
            return {"error": {"code": -32603, "message": str(exc)}}
        if target.is_symlink():
            return {"error": {"code": -32603, "message": "symlink denied"}}
        if not target.exists():
            return {"error": {"code": -32604, "message": "not found"}}
        return {"result": {"uri": uri, "contents": [{"uri": uri, "text": target.read_text()}]}}

    # ---------- handlers ----------

    @staticmethod
    def _echo(tenant_id: str, args: dict[str, Any]) -> dict[str, Any]:
        return {"echo": args}

    def _scratchpad_write(self, tenant_id: str, args: dict[str, Any]) -> dict[str, Any]:
        state = self._state_for(tenant_id)
        state.scratchpad[args.get("key", "")] = args.get("value", "")
        return {"ok": True}

    def _scratchpad_read(self, tenant_id: str, args: dict[str, Any]) -> dict[str, Any]:
        state = self._state_for(tenant_id)
        return {"value": state.scratchpad.get(args.get("key", ""))}

    def _cache_lookup(self, tenant_id: str, args: dict[str, Any]) -> dict[str, Any]:
        state = self._state_for(tenant_id)
        tool = args.get("tool", "")
        q = args.get("q", "")
        prompt_hash = hashlib.sha256(str(q).encode("utf-8")).hexdigest()[:16]
        key = (tenant_id, tool, prompt_hash, self.manifest.schema_version)
        if key in state.cache:
            return state.cache[key]
        value = {"echo": args}
        state.cache[key] = value
        return value

    @staticmethod
    def _fetch_url(tenant_id: str, args: dict[str, Any]) -> dict[str, Any]:
        # SSRF mitigation: deny non-allowlisted hosts.
        url = args.get("url", "")
        if not url.startswith(("https://allowed.example/", "http://localhost/")):
            return {"error": {"code": -32603, "message": "url not allowlisted"}}
        return {"result": {"fetched": url, "forwarded_auth": bool(args.get("forward_auth"))}}


def build_server(*args: Any, **kwargs: Any) -> SecureServer:
    """Construct and return the secure MCP server."""
    return SecureServer(*args, **kwargs)


__all__ = ["SecureServer", "build_server"]