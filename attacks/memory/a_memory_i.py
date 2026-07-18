"""Phase 7 concrete attack for memory boundary, STRIDE letter I (Information Disclosure).

Pattern: :func:`attacks._patterns.memory_attack` (specialised by STRIDE).

CVSS:3.1 vector: ``CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N``

Cross-references:
- ``docs/04_Attack_Taxonomy.md`` — per-boundary STRIDE table.
- ``docs/notes/mcp_learning/00_appendix.md`` — Phase-1 ticket catalogue.
"""

from __future__ import annotations

from attacks._helpers import AttackContext, dispatch_call, marker_match
from attacks.base import Attack, AttackResult
from framework.core.types import Boundary


class MemoryIAttack(Attack):
    """STRIDE row for the memory boundary, letter I (Information Disclosure).

    CVSS:3.1: ``CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N``
    """

    id = "A-MEM-I"
    boundary = Boundary.MEMORY
    cvss = "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N"

    async def setup(self, ctx: AttackContext) -> None:  # pragma: no cover - trivial
        # Concrete setup is a no-op for Phase 7; Phase 8 may add
        # connector-specific priming (e.g. open a session, populate a
        # scratchpad).
        return None

    async def execute(self, ctx: AttackContext) -> AttackResult:
        """Run the memory/I attack and return the result."""
        payload_marker = ctx.payload_marker

        # Memory / scratchpad cross-tenant leakage. The source
        # connector writes a value to a scratchpad keyed by name only
        # (no tenant_id); the sink connector reads the same key.
        sargs = {"key": payload_marker[:8], "value": payload_marker}
        sresp, slat = dispatch_call(ctx.source_connector, "scratchpad_write", sargs)
        rargs = {"key": payload_marker[:8]}
        rresp, rlat = dispatch_call(ctx.sink_connector, "scratchpad_read", rargs)
        success = marker_match(payload_marker, sresp) or marker_match(payload_marker, rresp)
        detail = {"write_response": sresp, "read_response": rresp,
                  "write_latency_ms": slat, "read_latency_ms": rlat}

        return AttackResult(success=bool(success), boundary=self.boundary, detail=detail)

    async def teardown(self, ctx: AttackContext) -> None:  # pragma: no cover - trivial
        return None
