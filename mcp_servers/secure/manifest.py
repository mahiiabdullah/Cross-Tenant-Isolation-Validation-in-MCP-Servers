"""Frozen manifest loader for the secure reference server.

Phase 8 ships the loader with signature verification
**deferred** (per the "Core deliverables only" scope chosen in
the Phase-8 plan). The manifest is read from
``mcp_servers/secure/manifest.json`` and validated against the
documented schema.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from framework.core.errors import ManifestError

logger = logging.getLogger(__name__)

EXPECTED_TOOLS = {"echo", "scratchpad_write", "scratchpad_read", "cache_lookup", "fetch_url"}


@dataclass
class FrozenManifest:
    """A frozen, versioned tool manifest."""

    schema_version: int
    tools: list[dict[str, Any]] = field(default_factory=list)

    def tool_names(self) -> set[str]:
        return {t["name"] for t in self.tools}


def load_manifest(path: Path) -> FrozenManifest:
    """Load and validate the manifest at ``path``."""
    if not path.exists():
        raise ManifestError(f"manifest not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    schema_version = raw.get("schema_version")
    if not isinstance(schema_version, int):
        raise ManifestError("manifest.schema_version must be int")
    tools = raw.get("tools", [])
    if not isinstance(tools, list):
        raise ManifestError("manifest.tools must be list")
    names = {t.get("name") for t in tools}
    missing = EXPECTED_TOOLS - names
    if missing:
        raise ManifestError(f"manifest missing required tools: {sorted(missing)}")
    logger.info("loaded frozen manifest schema_version=%d with %d tools", schema_version, len(tools))
    return FrozenManifest(schema_version=schema_version, tools=tools)


def verify_signature(manifest_bytes: bytes, signature: bytes, public_key: bytes) -> bool:
    """Verify the manifest signature. **DEFERRED to Phase 9+** (TODO)."""
    # TODO(phase-9): implement Ed25519 / RSA-PSS signature
    # verification using a real cryptography library. For Phase 8
    # we accept any non-empty signature so the loader can be
    # exercised end-to-end.
    return len(signature) > 0


__all__ = ["EXPECTED_TOOLS", "FrozenManifest", "load_manifest", "verify_signature"]