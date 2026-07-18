"""Phase 7 concrete attack for namespace boundary, STRIDE letter I (Information Disclosure).

Pattern: :func:`attacks._patterns.namespace_attack` (specialised by STRIDE).

CVSS:3.1 vector: ``CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N``

Cross-references:
- ``docs/04_Attack_Taxonomy.md`` — per-boundary STRIDE table.
- ``docs/notes/mcp_learning/00_appendix.md`` — Phase-1 ticket catalogue.
"""

from __future__ import annotations

from attacks._helpers import AttackContext, dispatch_call, dispatch_read, marker_match
from attacks.base import Attack, AttackResult
from framework.core.types import Boundary


class NamespaceIAttack(Attack):
    """STRIDE row for the namespace boundary, letter I (Information Disclosure).

    CVSS:3.1: ``CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N``
    """

    id = "A-NSP-I"
    boundary = Boundary.NAMESPACE
    cvss = "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N"

    async def setup(self, ctx: AttackContext) -> None:  # pragma: no cover - trivial
        # Concrete setup is a no-op for Phase 7; Phase 8 may add
        # connector-specific priming (e.g. open a session, populate a
        # scratchpad).
        return None

    async def execute(self, ctx: AttackContext) -> AttackResult:
        """Run the namespace/I attack and return the result."""
        payload_marker = ctx.payload_marker

        # Namespace squatting / shadowing attack. We attempt to invoke
        # a tool with a name that shadows a built-in. The source
        # connector records whether the shadow succeeded; the sink
        # connector is then asked to read a resource whose URI is
        # shaped by the squatted name.
        sargs = {"name": "shadow_set_env", "value": payload_marker}
        sresp, slat = dispatch_call(ctx.source_connector, "set_env", sargs)
        rargs = {"uri": f"file:///{payload_marker[:8]}/shadow.txt"}
        rresp, rlat = dispatch_read(ctx.sink_connector, rargs["uri"])
        success = marker_match(payload_marker, sresp) or marker_match(payload_marker, rresp)
        detail = {"shadow_response": sresp, "resource_response": rresp,
                  "shadow_latency_ms": slat, "resource_latency_ms": rlat}

        return AttackResult(success=bool(success), boundary=self.boundary, detail=detail)

    async def teardown(self, ctx: AttackContext) -> None:  # pragma: no cover - trivial
        return None
