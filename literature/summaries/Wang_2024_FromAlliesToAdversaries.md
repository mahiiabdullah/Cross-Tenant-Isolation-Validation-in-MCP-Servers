# Wang et al. 2024 — From Allies to Adversaries: Manipulating LLM Tool-Calling through Adversarial Injection

> **Citation status: VERIFIED** (arXiv abstract fetched 2026-07-18).
> Canonical URL: <https://arxiv.org/abs/2412.10198>

**arXiv ID:** 2412.10198

**Title:** From Allies to Adversaries: Manipulating LLM Tool-Calling
through Adversarial Injection

**Authors:** Haowei Wang, Rupeng Zhang, Junjie Wang, Mingyang Li,
Yuekai Huang, Dandan Wang, Qing Wang

**Year:** 2024

**Venue:** arXiv preprint

## Problem addressed

LLM tool-calling systems accept a natural-language intent, the LLM
selects a tool, and the system invokes it. The paper asks: how
vulnerable is the *tool-scheduling* decision itself, and what happens
when an adversary can inject attacker-controlled tools into the
registry that the LLM sees?

## Method

- Designed **ToolCommander**, a framework for adversarial tool
  injection that exploits LLM tool-scheduling mechanisms.
- Injected malicious tools alongside legitimate tools and measured
  hijack rates.
- Varied the injection positions, descriptions, and argument schemas.

## Key results

- LLM tool-scheduling is highly vulnerable to *injected* tools; the
  model's selection logic can be hijacked with well-described decoy
  tools.
- The attack succeeds even when the malicious tool's arguments
  differ semantically from the user's intent, because the model
  prioritises recency and description salience.
- Defenses that simply validate arguments are insufficient; the model
  must reason about tool *origin* and *trust*.

## Relevance to MCP isolation research

Directly maps to MCP's **namespace** and **tool** boundaries. MCP
servers that allow dynamic tool registration (as the planned
`vulnerable/server.py` does) are subject to exactly the attack this
paper describes: an attacker registers a tool with a salient
description that hijacks the dispatch decision. Phase-1 tickets
`A-NSP-001` (tool shadowing), `A-TOL-005` (handler-mismatch
invocation), and `A-NSP-007` (decorator-name shadowing) are the
MCP-specific instances of this general failure.

## Open questions for our work

- How does the attack behave when tools are namespaced per tenant?
- Does a "signed tool manifest" defense (as planned in
  `mcp_servers/secure/`) eliminate the hijack?
- Does the description-channel attack (`A-TOL-007`) compose with
  indirect prompt injection to escalate the impact?