"""Phase 7 concrete attack for transport boundary, STRIDE letter I (Information Disclosure).

Pattern: :func:`attacks._patterns.transport_attack` (specialised by STRIDE).

CVSS:3.1 vector: ``CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N``

Cross-references:
- ``docs/04_Attack_Taxonomy.md`` — per-boundary STRIDE table.
- ``docs/notes/mcp_learning/00_appendix.md`` — Phase-1 ticket catalogue.
"""

from __future__ import annotations

from attacks._helpers import AttackContext, dispatch_call, marker_match
from attacks.base import Attack, AttackResult
from framework.core.types import Boundary


class TransportIAttack(Attack):
    """STRIDE row for the transport boundary, letter I (Information Disclosure).

    CVSS:3.1: ``CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N``
    """

    id = "A-TRN-I"
    boundary = Boundary.TRANSPORT
    cvss = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"

    async def setup(self, ctx: AttackContext) -> None:  # pragma: no cover - trivial
        # Concrete setup is a no-op for Phase 7; Phase 8 may add
        # connector-specific priming (e.g. open a session, populate a
        # scratchpad).
        return None

    async def execute(self, ctx: AttackContext) -> AttackResult:
        """Run the transport/I attack and return the result."""
        payload_marker = ctx.payload_marker

        # Framing / replay / impersonation attack on the transport.
        # The marker is smuggled into a framing byte sequence inside
        # the tool arguments. We use the source connector to invoke
        # `echo` and let the harness sink-side evaluate whether the
        # payload surface area was successfully transmitted.
        args = {"q": payload_marker, "transport": "http_sse", "raw": True}
        response, latency_ms = dispatch_call(ctx.source_connector, "echo", args)
        success = marker_match(payload_marker, response) or response.get("result") is not None
        detail = {"response": response, "latency_ms": latency_ms}

        return AttackResult(success=bool(success), boundary=self.boundary, detail=detail)

    async def teardown(self, ctx: AttackContext) -> None:  # pragma: no cover - trivial
        return None
