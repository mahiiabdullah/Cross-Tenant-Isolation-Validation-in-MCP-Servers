"""Grammar-aware fuzzing harness for MCP surfaces.

Implements the methodology of LSPFuzz (Zhu et al. 2025) adapted
to MCP: well-formed JSON-RPC 2.0 envelopes with mutated parameter
shapes. Phase 9 will exercise this against the reference
servers.

CVSS:3.1: ``CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H``
"""

from __future__ import annotations

import random

from attacks._helpers import AttackContext, dispatch_call
from attacks.base import Attack, AttackResult
from framework.core.types import Boundary


class GrammarFuzzAttack(Attack):
    """Property-based fuzzing of the JSON-RPC envelope."""

    id = "A-FUZZ-001"
    boundary = Boundary.TRANSPORT  # fuzzes across all boundaries
    cvss = "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H"

    async def setup(self, ctx: AttackContext) -> None:  # pragma: no cover - trivial
        return None

    async def execute(self, ctx: AttackContext) -> AttackResult:
        marker = ctx.payload_marker
        n_mutations = max(1, ctx.parameters.get("n_mutations", 5))
        rng = random.Random((ctx.seed * 1_000_003) ^ hash(marker))
        results = []
        any_success = False
        for i in range(n_mutations):
            # Mutate a well-formed envelope.
            envelope = {
                "jsonrpc": "2.0",
                "id": rng.randrange(1 << 31),
                "method": rng.choice(["tools/call", "resources/read", "prompts/get"]),
                "params": {
                    "name": rng.choice(["echo", "set_env", "scratchpad_write", "cache_lookup"]),
                    "arguments": {
                        "marker": f"{marker}-{i}",
                        "fuzz_int": rng.choice([0, 1, -1, 2**31]),
                        "fuzz_str": "A" * rng.randrange(0, 1024),
                    },
                },
            }
            response, latency_ms = dispatch_call(
                ctx.source_connector,
                envelope["params"]["name"],
                envelope["params"]["arguments"],
            )
            ok = response.get("result") is not None and "error" not in response
            any_success = any_success or ok
            results.append(
                {
                    "envelope": envelope,
                    "response": response,
                    "latency_ms": latency_ms,
                    "ok": ok,
                }
            )
        return AttackResult(
            success=bool(any_success),
            boundary=self.boundary,
            detail={"n_mutations": n_mutations, "results": results},
        )

    async def teardown(self, ctx: AttackContext) -> None:  # pragma: no cover - trivial
        return None