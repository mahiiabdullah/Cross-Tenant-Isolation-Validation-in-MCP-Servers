# Zou et al. 2023 — Universal and Transferable Adversarial Attacks on Aligned Language Models

> **Citation status: VERIFIED** (arXiv abstract fetched 2026-07-18).
> Canonical URL: <https://arxiv.org/abs/2307.15043>

**arXiv ID:** 2307.15043

**Title:** Universal and Transferable Adversarial Attacks on Aligned
Language Models

**Authors:** Andy Zou, Zifan Wang, Nicholas Carlini, Milad Nasr,
J. Zico Kolter, Matt Fredrikson

**Year:** 2023

**Venue:** arXiv preprint

## Problem addressed

Prior jailbreak attacks against aligned LLMs required significant
human ingenuity and were brittle. This paper introduces a *gradient-
based* automated method to craft a single adversarial suffix that,
when appended to a user prompt, causes aligned LLMs (ChatGPT, Bard,
Claude, Llama-2) to produce objectionable content — and the suffix
*transfers* across models.

## Method

- Greedy coordinate-gradient (GCG) search over discrete tokens to
  minimise the model's likelihood of refusing the request while
  maximising the likelihood of an affirmative response.
- A single optimised suffix is appended to a wide range of prompts
  and across many models.

## Key results

- GCG suffixes reliably jailbreak aligned commercial LLMs at non-
  negligible rates.
- Suffixes transfer across models — a suffix optimised against one
  open-weight model succeeds on closed-weight commercial models.
- Defences built on perplexity filtering or simple output checks
  offer partial mitigation.

## Relevance to MCP isolation research

Although the paper targets model alignment rather than MCP isolation,
its methodological contribution — *automated, transferable attack
generation* — is directly relevant to our framework design (Phase 6).
GCG-style search is the analogue, in the prompt-injection space, of
the property-based fuzzing we plan for the transport and namespace
boundaries. The paper also shows that *prompt-side* attacks bypass
isolation guarantees that are enforced only at the *tool-side* — a
recurring failure mode in MCP deployments.

## Open questions for our work

- Can automated attack generation be combined with MCP-tool dispatch
  fuzzing to discover *composite* attacks (prompt-side + tool-side)
  that bypass per-layer defences?
- Do suffix-style attacks survive template rendering in `prompts/get`
  if the rendered prompt includes a substring with adversarial
  influence?
- How does the GCG transfer finding generalise to MCP's SDK
  divergence (Phase 1, Component 9): is an attack optimised against
  the Python SDK transferable to the TypeScript SDK?