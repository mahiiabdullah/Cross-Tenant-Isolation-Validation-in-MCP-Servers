# Lee et al. 2026 — WebMCP Tool Surface Poisoning

> **Citation status: VERIFIED** (arXiv abstract fetched 2026-07-18).
> Canonical URL: <https://arxiv.org/abs/2606.06387>

**arXiv ID:** 2606.06387

**Title:** WebMCP Tool Surface Poisoning: Runtime Manipulation Attacks
on LLM Agents

**Authors:** Lin-Fa Lee, Yi-Yu Chang, Chia-Mu Yu, Kuo-Hui Yeh

**Year:** 2026

**Venue:** arXiv preprint

## Problem addressed

WebMCP is a protocol variant that lets websites expose tools directly
to AI agents. The dynamic, third-party-script-driven exposure of
agent-accessible tools creates a novel attack surface in web
sessions.

## Method

- Identified and named a new attack class: **Mid-Session Tool
  Injection (MSTI)**.
- Adversaries leverage third-party scripts to inject malicious tools
  into the agent's tool registry *during* an active session.
- Implemented and evaluated the attack against representative WebMCP
  browser agent integrations.

## Key results

- Mid-session injection is achievable in real-world web sessions
  because the tool registry is mutable from JavaScript contexts.
- The attack bypasses pre-session tool allowlists (the malicious
  tool appears only after session establishment).
- Standard browser security (CSP, same-origin policy) is insufficient
  because the tool surface is exposed at a higher semantic layer
  than the DOM.

## Relevance to MCP isolation research

MCP itself does not run in the browser, but the architectural lesson
is directly applicable: **mutable tool registries create injection
windows that pre-session policies cannot cover**. This validates the
"frozen, signed manifest" defense planned for the secure reference
server (`mcp_servers/secure/server.py`) and motivates the
`notifications/tools/list_changed` event in MCP as a trust-relevant
signal (Phase 1, Component 2).

## Open questions for our work

- Does the MCP spec's `notifications/tools/list_changed` semantics
  provide a sufficient audit signal for detecting MSTI-style
  attacks?
- Can our framework (Phase 6) detect mid-session registry mutations
  as a leakage event, even when the new tool is "well-described"?