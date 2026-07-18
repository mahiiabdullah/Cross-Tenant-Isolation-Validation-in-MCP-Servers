# Greshake et al. 2023 — Not What You've Signed Up For

> **Citation status: VERIFIED** (arXiv abstract fetched 2026-07-18).
> Canonical URL: <https://arxiv.org/abs/2302.12173>

**arXiv ID:** 2302.12173

**Title:** Not what you've signed up for: Compromising Real-World
LLM-Integrated Applications with Indirect Prompt Injection

**Authors:** Kai Greshake, Sahar Abdelnabi, Shailesh Mishra,
Christoph Endres, Thorsten Holz, Mario Fritz

**Year:** 2023

**Venue:** arXiv preprint

## Problem addressed

The paper introduces **indirect prompt injection** as a distinct attack
class: rather than supplying adversarial text directly as the user
message, an attacker plants adversarial text in content the LLM later
reads via a tool, retrieval, or document fetch. The paper studies
real-world LLM-integrated applications (search-augmented chatbots,
email assistants) and shows that an attacker who can publish content
that the integrated application ingests can hijack the model's
behavior end-to-end.

## Method

- Threat-modelled three integration patterns: search augmentation,
  application-mediated tool use, and email/calendar agents.
- Built proof-of-concept exploits against each pattern, demonstrating
  data exfiltration, instruction override, and outbound action
  redirection.
- Proposed taxonomy distinguishing direct from indirect injection and
  explored mitigations (instructional separation, output filtering).

## Key results

- Indirect prompt injection is *not* a niche concern: the authors
  achieve realistic exploits across multiple production-style
  application shapes.
- Mitigations proposed by LLM providers at the time were brittle to
  even simple injection payloads.
- The work coined the term "indirect prompt injection" and is the
  canonical reference for the class.

## Relevance to MCP isolation research

This is the foundational paper for indirect prompt injection. In MCP
terms, indirect injection operates across the **tool**, **resource**,
and **memory** boundaries: an attacker controls a resource the
`resources/read` call returns, a tool result that `tools/call` returns,
or a cached entry that `memory` retains. Every Phase-1 ticket in
`docs/notes/mcp_learning/02_tools_routing.md` §E, `03_resources.md` §E,
and `04_prompts_context.md` §E traces back to the mechanism this paper
introduced.

## Open questions for our work

- How does indirect injection behave when the model has multiple
  tool namespaces per tenant (MCP's per-tenant tool registry)?
- Can MCP's `prompts/get` boundary serve as an effective mitigation
  by allowing only enumerated, signed prompts to be rendered?
- Does the cross-tenant cache failure mode (`A-CCH-001`,
  `A-CCH-003`) extend the indirect injection threat from "single
  attacker / single victim" to "single attacker / many victims
  via cache poisoning"?