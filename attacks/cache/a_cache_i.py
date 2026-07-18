"""Phase 7 concrete attack for cache boundary, STRIDE letter I (Information Disclosure).

Pattern: :func:`attacks._patterns.cache_attack` (specialised by STRIDE).

CVSS:3.1 vector: ``CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N``

Cross-references:
- ``docs/04_Attack_Taxonomy.md`` — per-boundary STRIDE table.
- ``docs/notes/mcp_learning/00_appendix.md`` — Phase-1 ticket catalogue.
"""

from __future__ import annotations

from attacks._helpers import AttackContext, dispatch_call, marker_match
from attacks.base import Attack, AttackResult
from framework.core.types import Boundary


class CacheIAttack(Attack):
    """STRIDE row for the cache boundary, letter I (Information Disclosure).

    CVSS:3.1: ``CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N``
    """

    id = "A-CCH-I"
    boundary = Boundary.CACHE
    cvss = "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N"

    async def setup(self, ctx: AttackContext) -> None:  # pragma: no cover - trivial
        # Concrete setup is a no-op for Phase 7; Phase 8 may add
        # connector-specific priming (e.g. open a session, populate a
        # scratchpad).
        return None

    async def execute(self, ctx: AttackContext) -> AttackResult:
        """Run the cache/I attack and return the result."""
        payload_marker = ctx.payload_marker

        # Cache key collision attack. Both connectors attempt to read
        # the same cache entry keyed by (tool_name, args_hash); the
        # attack succeeds if the sink returns the source's payload.
        sargs = {"tool": "lookup", "q": payload_marker}
        sresp, slat = dispatch_call(ctx.source_connector, "cache_lookup", sargs)
        rresp, rlat = dispatch_call(ctx.sink_connector, "cache_lookup", sargs)
        success = marker_match(payload_marker, sresp) or marker_match(payload_marker, rresp)
        detail = {"source_lookup": sresp, "sink_lookup": rresp,
                  "source_latency_ms": slat, "sink_latency_ms": rlat}

        return AttackResult(success=bool(success), boundary=self.boundary, detail=detail)

    async def teardown(self, ctx: AttackContext) -> None:  # pragma: no cover - trivial
        return None
