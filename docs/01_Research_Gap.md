# 01 — Research Gap

> Phase 3 deliverable. Extended from the prior TBD stub with the
> one-sentence research-gap statement derived from
> `literature/related_work.md`.

## Status

Filled during Phase 3 (Literature Review). All citations supporting
the gap analysis are listed in `literature/bibliography.bib` and
summarised in `literature/summaries/`.

## Open Questions

- How is isolation currently characterised in MCP specification
  documents and SDKs?
  - **Status:** answered by Phase 1 (`docs/notes/mcp_learning/`) —
    isolation is implicitly distributed across eight boundaries,
    none of which is mandated by the spec.
- What do adjacent protocols (LSP, IPC, RPC) teach us about
  isolation guarantees?
  - **Status:** partially answered by Zhu et al. (2025, LSPFuzz,
    `literature/summaries/Zhu_2025_LSPFuzz.md`) — LSP's
    architecture is the closest analogue and inherits many of the
    same JSON-RPC pitfalls.
- Which isolation failures have been observed in deployed MCP
  servers (if any)?
  - **Status:** answered empirically by Chen et al. (2026,
    `literature/summaries/Chen_2026_RethinkingMCPSecurity.md`) —
    shared stdio workers, symlink-following resolvers, and
    cache keys without tenant identity are observed at scale.
- What defenses exist in mainstream MCP client libraries?
  - **Status:** answered by An et al. (2026,
    `literature/summaries/An_2026_FlowGuardMCPSecurity.md`) —
    mainstream scanners reason about semantic signals and miss
    runtime behaviours.

## Candidate Gaps (with status)

- [x] **No formal isolation model for MCP tenants.**
  - Phase 1 catalogued the eight implicit boundaries; Phase 5 will
    produce a formal STRIDE enumeration per boundary.
- [x] **No standardised leakage metrics for MCP boundaries.**
  - Phase 6 (framework design) will define `leakage_rate`,
    `time_to_leak`, `defense_overhead`, and `utility_retention`
    metrics.
- [x] **No public benchmark corpus of MCP isolation attacks.**
  - Phase 7 (attack library) will produce ≥25 attack classes; the
    framework's runnable harness (Phase 8) will serve as a
    reproducible benchmark.
- [x] **No empirical comparison of defense strategies.**
  - Phase 9 (experiments) will run the attack library against
    vulnerable and secure reference servers (Phase 8).

## Research Gap (one sentence)

> **No prior work has systematically catalogued MCP isolation
> failures across all eight protocol boundaries, mapped them to
> automated attack patterns, and empirically measured their
> leakage under a reproducible multi-tenant harness.**

This sentence is reproduced verbatim in
`literature/related_work.md` (Research Gap section) and will be
reproduced in the paper's introduction (Phase 11) and discussion
(Phase 11).

---

## Novelty Score (Phase 4 addendum)

> Added in Phase 4 per the prompt's Done-When gate:
> *"A novelty score with justification is recorded in
> `docs/01_Research_Gap.md`."* Full novelty document at
> `docs/notes/novelty/00_novelty.md`.

### Score: **8 / 10**

### Yes/No answers (one citation each, all VERIFIED 2026-07-18)

| # | Question | Answer | Closest prior paper |
| --- | --- | --- | --- |
| Q1 | Has anyone built an automated red-teaming suite specifically for MCP? | **NO** | Chen et al. 2026 (arXiv:2607.11086) — they benchmark static scanners, not runtime attacks. |
| Q2 | Has the community formally modeled MCP multi-tenant trust boundaries? | **NO** | Jing et al. 2026 (arXiv:2607.12406) — 5-boundary LLM-agent taxonomy, not MCP-specific. |
| Q3 | Are there baseline metrics for MCP cross-tenant context leakage? | **NO** | Dipta et al. 2024 (arXiv:2404.10715) — OS-sandbox side channels, not protocol leakage. |

### Justification (against the prompt's four targets)

- ✅ **Taxonomy covering all eight boundaries** — Phase 1 complete
  (`docs/02_Threat_Model.md`).
- 🔜 **Empirical measurement framework for MCP isolation** —
  Phase 6 design, Phase 9 execution.
- 🔜 **Defense comparison at the MCP layer (not OS layer)** —
  Phase 8 implementation, Phase 9 execution.
- 🔜 **Open-source artifact passing fresh-machine reproduction** —
  Phase 8 build, Phase 9 reproducibility gate.

8/10 reflects that the **conceptual scaffolding is complete and
defensible** (Phases 1–3) but the **empirical claims** (which
carry the bulk of novelty weight at a security venue) are pending
execution (Phases 8–9).

A score of **9** would require at least one executed leakage
number; **10** would additionally require field-deployment
evidence (honestly out of scope).

---

## Contributions (Phase 4 addendum)

> Added in Phase 4. Full justification, evidence, and
> delta-vs-prior statements in `docs/notes/novelty/00_novelty.md`.
> Phase 11 will paste this list into
> `paper/sections/01_introduction.tex`.

1. **A complete isolation-boundary catalogue for the Model Context
   Protocol**, covering all eight boundaries (transport, session,
   namespace, tool, resource, memory, cache, auth) with a
   STRIDE-tagged attack surface per boundary and 63 forward ticket
   IDs (`A-{TRN,SES,NSP,TOL,RES,MEM,CCH,AUT}-{nnn}`).
   *Delta vs. prior work:* Jing et al. 2026 propose 5 generic
   LLM-agent boundaries; ours is 8 MCP-specific boundaries with
   STRIDE rows.

2. **A 14-concept security taxonomy with explicit MCP-boundary
   bindings**, pinning each concept (direct prompt injection,
   indirect prompt injection, jailbreaking, confused deputy,
   capability-based access control, sandbox escaping, side-channel
   leakage, cache poisoning, memory poisoning, namespace
   collision, tool squatting, resource traversal, request
   smuggling, authentication bypass) to one or more MCP boundaries.
   *Delta vs. prior work:* OWASP LLM Top 10 v1.1 is
   LLM-application-level, not protocol-level; no prior work pins
   security concepts to MCP boundaries.

3. **A reproducible empirical framework that measures cross-tenant
   leakage in MCP deployments** under controlled multi-tenant
   concurrency, reporting `leakage_rate`, `time_to_leak`,
   `defense_overhead`, and `utility_retention` per boundary.
   *Delta vs. prior work:* Chen et al. 2026 measure single-tenant
   MCP-server risk; An et al. 2026 (FlowGuard) detect but do not
   measure leakage; Liu et al. 2026 (MCPEvol-Bench) study tool
   evolution, not tenant isolation.

4. **An open attack library of ≥25 concrete attack classes**
   covering every MCP boundary, each with CVSS scoring and pytest
   reproducibility.
   *Delta vs. prior work:* Wang et al. 2024, Torres et al. 2026,
   and Lee et al. 2026 each demonstrate *one* failure mode in
   isolation; no prior work composes them into a single library
   with uniform pytest reproducibility.

5. **A defence-comparison study at the MCP layer** (not the OS
   layer) quantifying the leakage reduction achieved by per-tenant
   tool registries, tenant-prefixed cache keys, resource-path
   canonicalisation, and mTLS — individually and in composition.
   *Delta vs. prior work:* Dipta et al. 2024 study OS-level
   sandbox side channels; ours is protocol-level and measures
   leakage reduction.