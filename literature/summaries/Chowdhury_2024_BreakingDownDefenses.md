# Chowdhury et al. 2024 — Breaking Down the Defenses: A Comparative Survey of Attacks on LLMs

> **Citation status: VERIFIED** (arXiv abstract fetched 2026-07-18).
> Canonical URL: <https://arxiv.org/abs/2403.04786>

**arXiv ID:** 2403.04786

**Title:** Breaking Down the Defenses: A Comparative Survey of Attacks
on Large Language Models

**Authors:** Arijit Ghosh Chowdhury, Md Mofijul Islam, Vaibhav Kumar,
Faysal Hossain Shezan, Vinija Jain, Aman Chadha

**Year:** 2024

**Venue:** arXiv preprint

## Problem addressed

The LLM attack literature has grown rapidly; new attack families
(jailbreaks, prompt injection, data extraction, model stealing,
backdoors) emerge faster than defenses. This survey systematises the
attack surface and evaluates existing defenses against a comparable
set of attacks.

## Method

- Literature-driven taxonomy of attacks and defenses.
- Reproduced several attacks and defenses under a uniform evaluation
  harness.
- Cross-cut analysis: which defenses hold up against *which*
  attacks.

## Key results

- Defenses that work in isolation (e.g. perplexity filtering) often
  fail under composition with other defenses or against new attacks.
- The attack surface extends well beyond the model: training data,
  embeddings, tools, retrieval content, and system prompts all
  contribute.
- Quantitative defense effectiveness varies substantially across
  attack families.

## Relevance to MCP isolation research

The survey's defence-evaluation methodology is a direct precedent
for our Phase 9 (experiments) and Phase 12 (reviewer simulation)
protocols. The finding that defenses fail under composition is
directly relevant to MCP, which composes eight independent isolation
boundaries: each boundary has known defenses, but their composition
is rarely evaluated.

## Open questions for our work

- Which composition of MCP-layer defenses (per-tenant tool registry +
  cache key namespacing + resource path canonicalisation + mTLS)
  yields non-trivial coverage of the STRIDE space?
- Can we reproduce the survey's defense-collapse finding at the MCP
  layer with our vulnerable vs. secure reference servers?
- Does the survey's evaluation harness translate to MCP, where the
  attack surface is structural rather than textual?