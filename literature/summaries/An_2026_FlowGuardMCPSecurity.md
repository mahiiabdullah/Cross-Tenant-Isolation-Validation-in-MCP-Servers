# An et al. 2026 — FlowGuard: From Signals to Evidence for MCP Security Detection

> **Citation status: VERIFIED** (arXiv abstract fetched 2026-07-18).
> Canonical URL: <https://arxiv.org/abs/2607.14754>

**arXiv ID:** 2607.14754

**Title:** FlowGuard: From Signals to Evidence for MCP Security
Detection

**Authors:** Baichao An, Pei Chen, Geng Hong, Yueyue Chen, Mengying Wu

**Year:** 2026

**Venue:** arXiv preprint

## Problem addressed

Existing MCP security scanners detect suspicious *semantic signals*
(e.g. credential-like strings, suspicious tool names) but cannot
connect these signals to actual execution behavior, leading to high
false-positive rates and missed true positives. This paper proposes
**FlowGuard**, a runtime evidence-collection framework for MCP.

## Method

- Instruments MCP servers to collect *behavioral traces* alongside
  semantic signals.
- Correlates semantic signals with downstream execution behavior to
  produce evidence-grade risk assessments.
- Evaluates against a benchmark of known MCP-server risk patterns.

## Key results

- Signal-only scanners produce unreliable risk assessments (in line
  with Chen et al. 2026).
- Behavior-trace correlation substantially reduces false-positive
  rate without sacrificing recall.
- Several common MCP-server patterns (per Chen et al.) generate
  consistent evidence signatures under FlowGuard.

## Relevance to MCP isolation research

Directly motivates the *Evaluator* module of our framework (Phase 6).
Our framework's `framework/evaluator/evaluator.py` is the
generalisation of FlowGuard: instead of detecting "MCP-server risk"
in the abstract, we detect cross-tenant *leakage events*. FlowGuard
provides a precedent for evidence-driven detection and a baseline
against which we can compare our leakage-event oracle.

## Open questions for our work

- Can the FlowGuard-style evidence trace be reused as the leakage
  signal in our Evaluator? What additional signals are needed?
- How do we avoid FlowGuard's signal-collection overhead in the
  high-concurrency scenarios our Phase 9 experiments plan?
- Does FlowGuard's evidence-grade approach generalise beyond MCP
  server tools to MCP resources and prompts?