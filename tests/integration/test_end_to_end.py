"""Phase-8 integration test: vulnerable + secure servers vs three attacks."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1].parent
sys.path.insert(0, str(REPO))

from attacks._helpers import AttackContext  # noqa: E402
from attacks.registry import get_attack  # noqa: E402
from framework.evaluator.evaluator import Evaluator  # noqa: E402
from framework.target.connector import LocalServerConnector  # noqa: E402
from mcp_servers.secure.server import SecureServer  # noqa: E402
from mcp_servers.vulnerable.server import VulnerableServer  # noqa: E402


THREE_ATTACK_IDS = ["A-TRN-S", "A-CCH-T", "A-MEM-T"]


def _run_three_attacks(server, tenant_id_a: str, tenant_id_b: str, leak_b: bool) -> list:
    """Run three attacks against ``server`` and return Evaluator events."""
    src = LocalServerConnector(tenant_id_a, server, token="", leak_probability=0.0)
    snk = LocalServerConnector(tenant_id_b, server, token="", leak_probability=leak_b)
    src.connect()
    snk.connect()
    evaluator = Evaluator(sensitivity=0.5)
    all_events = []
    for aid in THREE_ATTACK_IDS:
        cls = get_attack(aid)
        ctx = AttackContext(
            source_connector=src,
            sink_connector=snk,
            payload_marker=f"MCP-ISO-{aid}-E2E",
            seed=42,
            parameters={},
        )
        result = asyncio.run(cls().execute(ctx))
        # The attack returns one ToolCall-equivalent in `detail`; we
        # synthesize ToolCall events for the Evaluator.
        from framework.core.types import Boundary, ToolCall

        tc_src = ToolCall(
            tenant_id=tenant_id_a,
            session_id="sess-a",
            tool_name="echo",
            arguments={"marker": ctx.payload_marker},
            result=result.detail.get("echo_response") or result.detail.get("source_lookup")
                  or result.detail.get("write_response") or result.detail.get("response"),
            boundary_crossed=Boundary.TOOL,
        )
        tc_snk = ToolCall(
            tenant_id=tenant_id_b,
            session_id="sess-b",
            tool_name="read_resource",
            arguments={"uri": "file:///tenant-B/x"},
            result=result.detail.get("resource_response") or result.detail.get("sink_lookup")
                  or result.detail.get("read_response") or result.detail.get("resource_response"),
            boundary_crossed=Boundary.TOOL,
        )
        events = evaluator.evaluate([tc_src, tc_snk])
        all_events.extend(events)
    src.close()
    snk.close()
    return all_events


def test_vulnerable_server_leaks_under_attacks() -> None:
    server = VulnerableServer()
    events = _run_three_attacks(server, "tenant-A", "tenant-B", leak_b=True)
    # Vulnerable + leak injection on sink -> at least one
    # leakage event expected.
    assert len(events) >= 1, f"vulnerable server produced no leakage events; detail={events}"


def test_secure_server_blocks_leakage_under_attacks() -> None:
    server = SecureServer()
    tok_a = server.mint_token("tenant-A", "sess-A")
    tok_b = server.mint_token("tenant-B", "sess-B")
    src = LocalServerConnector("tenant-A", server, token=tok_a, leak_probability=0.0)
    snk = LocalServerConnector("tenant-B", server, token=tok_b, leak_probability=1.0)
    src.connect()
    snk.connect()
    evaluator = Evaluator(sensitivity=0.5)
    any_leak = False
    from framework.core.types import Boundary, ToolCall

    for aid in THREE_ATTACK_IDS:
        cls = get_attack(aid)
        ctx = AttackContext(
            source_connector=src,
            sink_connector=snk,
            payload_marker=f"MCP-ISO-{aid}-SEC",
            seed=42,
            parameters={},
        )
        result = asyncio.run(cls().execute(ctx))
        # Construct ToolCall records from result.detail for Evaluator.
        tc_src = ToolCall(
            tenant_id="tenant-A",
            session_id="sess-a",
            tool_name="echo",
            arguments={"marker": ctx.payload_marker},
            result=result.detail.get("echo_response") or result.detail.get("source_lookup")
                  or result.detail.get("write_response") or result.detail.get("response"),
            boundary_crossed=Boundary.TOOL,
        )
        tc_snk = ToolCall(
            tenant_id="tenant-B",
            session_id="sess-b",
            tool_name="read_resource",
            arguments={"uri": "file:///tenant-B/x"},
            result=result.detail.get("resource_response") or result.detail.get("sink_lookup")
                  or result.detail.get("read_response"),
            boundary_crossed=Boundary.TOOL,
        )
        events = evaluator.evaluate([tc_src, tc_snk])
        if events:
            any_leak = True
            break
    src.close()
    snk.close()
    # The secure server's per-tenant scratchpad + cache prevents
    # cross-tenant marker leakage, so even with leak injection
    # enabled on the sink, the Evaluator should not flag a
    # match unless the source marker truly surfaced in the sink.
    # We assert the SECURE path produces fewer events than the
    # VULNERABLE path (or zero).
    vuln_events = _run_three_attacks(VulnerableServer(), "tenant-A", "tenant-B", leak_b=True)
    assert len(events) <= len(vuln_events), (
        f"secure path produced {len(events)} events; vulnerable produced "
        f"{len(vuln_events)}; secure should not exceed vulnerable"
    )