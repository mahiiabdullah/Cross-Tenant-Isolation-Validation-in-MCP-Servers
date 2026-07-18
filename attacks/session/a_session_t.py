"""Phase 7 concrete attack for session boundary, STRIDE letter T (Tampering).

Pattern: :func:`attacks._patterns.session_attack` (specialised by STRIDE).

CVSS:3.1 vector: ``CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:N/I:H/A:N``

Cross-references:
- ``docs/04_Attack_Taxonomy.md`` — per-boundary STRIDE table.
- ``docs/notes/mcp_learning/00_appendix.md`` — Phase-1 ticket catalogue.
"""

from __future__ import annotations

from attacks._helpers import AttackContext, dispatch_call, dispatch_read, marker_match
from attacks.base import Attack, AttackResult
from framework.core.types import Boundary


class SessionTAttack(Attack):
    """STRIDE row for the session boundary, letter T (Tampering).

    CVSS:3.1: ``CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:N/I:H/A:N``
    """

    id = "A-SES-T"
    boundary = Boundary.SESSION
    cvss = "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:N/I:H/A:N"

    async def setup(self, ctx: AttackContext) -> None:  # pragma: no cover - trivial
        # Concrete setup is a no-op for Phase 7; Phase 8 may add
        # connector-specific priming (e.g. open a session, populate a
        # scratchpad).
        return None

    async def execute(self, ctx: AttackContext) -> AttackResult:
        """Run the session/T attack and return the result."""
        payload_marker = ctx.payload_marker

        # Session fixation / ID-reuse attack. We force a fixed session
        # id on the source connector and inspect whether the sink
        # connector's session store returns the same payload marker.
        # (Real connector implementation lands in Phase 8; here we
        # exercise the in-process state.)
        sargs = {"session_id": "fixed-deadbeef", "marker": payload_marker}
        sresp, slat = dispatch_call(ctx.source_connector, "echo", sargs)
        rargs = {"uri": f"file:///victim/{payload_marker[:8]}.txt"}
        rresp, rlat = dispatch_read(ctx.sink_connector, rargs["uri"])
        success = marker_match(payload_marker, rresp) or marker_match(payload_marker, sresp)
        detail = {"session_response": sresp, "resource_response": rresp,
                  "session_latency_ms": slat, "resource_latency_ms": rlat}

        return AttackResult(success=bool(success), boundary=self.boundary, detail=detail)

    async def teardown(self, ctx: AttackContext) -> None:  # pragma: no cover - trivial
        return None
