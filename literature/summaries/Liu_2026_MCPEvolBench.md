# Liu et al. 2026 — MCPEvol-Bench

> **Citation status: VERIFIED** (arXiv abstract fetched 2026-07-18).
> Canonical URL: <https://arxiv.org/abs/2607.14642>

**arXiv ID:** 2607.14642

**Title:** MCPEvol-Bench: Benchmarking LLM Agent Performance Across
Dynamic Evolutions of MCP Servers

**Authors:** Huanxi Liu, Kun Hu, Jiaqi Liao, Qiang Wang,
Pengfei Qian, YuanZhao Zhai, Dawei Feng, Bo Ding, Huaimin Wang

**Year:** 2026

**Venue:** arXiv preprint

## Problem addressed

Existing MCP benchmarks evaluate LLM agents against *static* MCP
servers. Real MCP servers evolve — tools are added, removed, and
modified continuously. The paper argues that current benchmarks
fail to capture an agent's adaptability in changing tool landscapes
and proposes **MCPEvol-Bench**, which evaluates agents under dynamic
tool evolution.

## Method

- Built a benchmark in which the MCP server's tool surface evolves
  over the course of an evaluation run.
- Measured agent performance (task completion, tool selection
  accuracy, robustness) across evolution steps.
- Compared agents that handle evolution explicitly vs. naively.

## Key results

- Static-evaluation benchmarks overstate agent robustness.
- Agents that explicitly handle tool-evolution signals
  (`notifications/tools/list_changed`) substantially outperform
  naive agents under server evolution.
- Some agents catastrophically fail when the *name* of a tool they
  previously relied on changes — directly relevant to the
  namespace-shadowing family (`A-NSP-001`).

## Relevance to MCP isolation research

Provides a benchmark precedent for our framework. The dynamic-
evolution angle suggests that our attack library (Phase 7) should
include mid-session registry mutations (cf. MSTI in Lee et al.
2026) and that our secure reference server's signed-manifest defense
should be evaluated under such mutations.

## Open questions for our work

- Can MCPEvol-Bench's evolution events serve as a *trigger* for
  attack conditions in our framework?
- Does the catastrophic-failure-on-rename finding imply that
  tool-name stability is itself a security property?
- How does the framework's per-tenant tool registry interact with
  the evolution model — is each tenant's registry evolved
  independently?