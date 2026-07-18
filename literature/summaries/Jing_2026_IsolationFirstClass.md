# Jing et al. 2026 — Isolation as a First-Class Principle for LLM-Agent System Safety

> **Citation status: VERIFIED** (arXiv abstract fetched 2026-07-18).
> Canonical URL: <https://arxiv.org/abs/2607.12406>

**arXiv ID:** 2607.12406

**Title:** Isolation as a First-Class Principle for LLM-Agent System
Safety: Concepts, Taxonomy, Challenges and Future Directions

**Authors:** Huihao Jing, Wenbin Hu, Shaojin Chen, Haochen Shi,
Sirui Zhang, Hanyu Yang, Changxuan Fan, Zhongwei Xie,
Hongyu Luo, Wun Yu Chan, Wei Fan, Haoran Li, Yangqiu Song

**Year:** 2026

**Venue:** arXiv preprint

## Problem addressed

The capability of LLM agents to function as the "brain" of a system
expands the scope of safety analysis beyond input-output alignment
to system behaviour and real-world execution outcomes. The current
literature is fragmented across attack types, applications, and
benchmarks; the paper argues that *isolation* should be elevated
from an implicit property to a **first-class design principle** for
LLM-agent system safety.

## Method

- Systematised the LLM-agent safety literature along isolation
  dimensions (process, data, control, trust).
- Proposed a taxonomy of isolation failures mapped to agent
  architectures.
- Identified open research challenges and future directions.

## Key results

- Many reported LLM-agent safety failures reduce to isolation
  failures (the same conclusion our Phase 1 work derives
  independently from MCP spec analysis).
- Defenses that treat isolation as a first-class property — with
  explicit enforcement, measurement, and recovery — outperform
  defences that treat it as a side effect of perimeter security.
- Open problems include cross-tenant isolation in shared agent
  runtimes, isolation-aware tool registries, and isolation-aware
  memory architectures.

## Relevance to MCP isolation research

This is the **single most directly on-topic paper** for our work.
Jing et al.'s call for "isolation as a first-class principle"
exactly matches our framing. The taxonomy they propose overlaps
significantly with our Phase 2 macro-categories (Isolation,
Architecture, Logic). We will reference this paper repeatedly in
the paper's introduction (Phase 11) and discussion (Phase 9).

## Open questions for our work

- Can we extend Jing et al.'s taxonomy from "LLM-agent systems"
  generally to MCP specifically (the eight MCP boundaries)?
- Do Jing et al.'s "isolation-aware tool registries" align with
  our planned per-tenant registry defense?
- Does Jing et al. propose quantitative leakage metrics that we
  can adopt directly in our Phase 9 experiments?