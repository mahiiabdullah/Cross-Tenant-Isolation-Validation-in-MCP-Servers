# 00 — Novelty Validation

> **Phase 4 deliverable.** Converts the Phase-3 research gap into
> defensible novelty claims for the paper *"Automated Cross-Tenant
> Isolation Validation in MCP Servers."* All citations are from the
> Phase-3 verified bibliography (`literature/bibliography.bib`,
> `literature/related_work.md`) — **no fabricated citations**.

## Status

Filled during Phase 4. Phase-3 evidence has been **re-verified** on
2026-07-18 via WebFetch on each cited arXiv abstract page; see the
"Verification log" section at the end of this document.

The four-phase novelty gate requires:

1. Three yes/no answers with one citation each (or "no prior work
   found").
2. A novelty score (1–10) with justification.
3. A list of strategic pivots (3–5 items).
4. A formal contributions list (3–5 numbered claims).

All four gates are satisfied below.

## Three Definitive Answers

### Q1 — Has anyone already built an automated red-teaming suite specifically for MCP?

**Answer: NO.**

**Closest prior paper:** Chen et al. 2026, *"Rethinking MCP
Security: A Large-Scale Study of Runtime MCP Servers and Security
Scanner Reliability"* (arXiv:2607.11086, VERIFIED via WebFetch on
2026-07-18).

**Evidence quote (verbatim from arXiv abstract):**

> *"the first ecosystem-scale measurement of MCP servers and the
> scanners that analyze them"*

**Delta vs. our work.** Chen et al. measure *server-level defaults*
and the *reliability of static scanners*; their contribution is a
*scanner benchmark* and a *corpus characterisation*, not a
*red-teaming harness* that drives multi-tenant attacks and
quantifies the resulting leakage. Our Phase-7 attack library and
Phase-9 evaluation harness will (a) drive ≥25 attack classes at
each MCP boundary, (b) measure cross-tenant leakage rate under
controlled concurrency, and (c) report per-attack CVSS and
defence-overhead numbers. None of (a)–(c) is in Chen et al.

> **Citation:** `chen_2026_mcp_security` in
> `literature/bibliography.bib`; summary in
> `literature/summaries/Chen_2026_RethinkingMCPSecurity.md`.

### Q2 — Has the community formally modeled MCP multi-tenant trust boundaries?

**Answer: NO.**

**Closest prior paper:** Jing et al. 2026, *"Isolation as a
First-Class Principle for LLM-Agent System Safety: Concepts,
Taxonomy, Challenges and Future Directions"* (arXiv:2607.12406,
VERIFIED via WebFetch on 2026-07-18).

**Evidence quote (verbatim from arXiv abstract):**

> *"a boundary-centric taxonomy of five boundaries: user-agent,
> agent-tool, agent-execution, agent-agent, and system-environment"*

**Delta vs. our work.** Jing et al. propose a 5-boundary taxonomy
for *LLM-agent systems generally*; their boundaries (user-agent,
agent-tool, agent-execution, agent-agent, system-environment) are
not MCP-specific and they do not include the MCP-native boundaries
we catalogued in Phase 1 — transport framing, JSON-RPC session,
namespace/registry, tool descriptor, resource resolver, agent
memory, response cache, and authentication/authorisation. Our
boundary catalogue is **MCP-specific, eight boundaries, with
STRIDE rows per boundary** (`docs/02_Threat_Model.md`, Phase 1).
The Jing et al. paper provides neither MCP-specific boundaries nor
a formal trust-boundary model with STRIDE.

> **Citation:** `jing_2026_isolation` in
> `literature/bibliography.bib`; see Cluster B in
> `literature/related_work.md`.

### Q3 — Are there existing baseline metrics for MCP cross-tenant context leakage?

**Answer: NO.**

**Closest prior paper:** Dipta et al. 2024, *"Dynamic
Frequency-Based Fingerprinting Attacks against Modern Sandbox
Environments"* (arXiv:2404.10715, VERIFIED via WebFetch on
2026-07-18).

**Evidence quote (verbatim from arXiv abstract):**

> *"a generic dynamic frequency-based fingerprinting attack that
> can defeat various state-of-the-art sandboxing technologies,
> including gVisor, Firecracker, SGX, and SEV"*

**Delta vs. our work.** Dipta et al. measure *side-channel
leakage from OS-level sandboxing primitives*; their metrics are
side-channel-specific (cache-line frequency, page-fault timing)
and their setting is *physical* isolation, not *protocol-level*
multi-tenant isolation. We will define MCP-native leakage
metrics — `leakage_rate`, `time_to_leak`, `defense_overhead`, and
`utility_retention` — and apply them at the *protocol* layer
(transport, session, namespace, tool, resource, memory, cache,
auth), not the *OS* layer. Dipta et al.'s metrics are not
transferable to MCP because they target kernel-visible timing
side channels rather than JSON-RPC payload leakage.

> **Citation:** `dipta_2024_sandbox` in
> `literature/bibliography.bib`; see Cluster D in
> `literature/related_work.md`.

## Summary of Answers

| Q | Answer | Closest paper | Why we differ |
| --- | --- | --- | --- |
| Q1 — automated MCP red-teaming | NO | Chen et al. 2026 | They benchmark static scanners; we drive runtime attacks and quantify leakage. |
| Q2 — formal MCP trust-boundary model | NO | Jing et al. 2026 | They have 5 generic LLM-agent boundaries; we have 8 MCP-specific boundaries with STRIDE rows. |
| Q3 — MCP cross-tenant leakage metrics | NO | Dipta et al. 2024 | They measure OS-sandbox side channels; we measure protocol-level leakage under multi-tenant concurrency. |

## Novelty Score

### Score: **8 / 10**

### Justification (against the prompt's four targets)

| Target | Status | Evidence |
| --- | --- | --- |
| Empirical measurement framework for MCP isolation | 🔜 Planned (Phase 6) | `framework/` directory not yet created; design documented in this Phase-4 plan. |
| Taxonomy covering all eight boundaries | ✅ Complete (Phase 1) | `docs/02_Threat_Model.md` boundary table; `docs/notes/mcp_learning/00_appendix.md` cross-component ticket index. |
| Defense comparison at the MCP layer (not OS layer) | 🔜 Planned (Phases 8–9) | `mcp_servers/vulnerable/` and `mcp_servers/secure/` not yet created; design follows Cluster D evidence. |
| Open-source artifact passing a fresh-machine reproduction test | 🔜 Planned (Phases 8–9) | Reproduction recipe will live in `README.md` and `reproduce.sh` (Phase 8). |

### What the 8/10 means

- **8/10 = strong conceptual scaffolding with pending empirical
  execution.** Phases 1–3 are complete (boundary catalogue, security
  taxonomy, verified literature, gap statement) — this is what a
  reviewer would call *"the conceptual novelty is defensible."*
- The two points lost are for **quantitative leakage measurements
  (no real numbers yet)** and **fresh-machine reproduction**
  (artifact not yet built). Phase 9 will provide the first; Phase 8
  + the reproducibility gate will provide the second.
- A score of **9** would require (a) at least one execution
  number, (b) a public-artifact reproducibility pass.
- A score of **10** would additionally require **field deployment
  evidence** (production MCP server telemetry) — this is **out of
  scope** for an academic reproduction study and is honestly
  disclosed as a limitation.

### Why not lower

- All three yes/no questions answered NO with a defensible citation.
- No fabricated citations; every claim is reproducible from
  `bibliography.bib`.
- The four targets in the prompt are tracked individually in the
  evidence table above.

## Strategic Pivots (5 items)

To push the novelty score from 8 toward 9–10 at a top security
venue (ACM CCS, IEEE S&P, USENIX Security, NDSS), the project
**must include** the following:

1. **Quantify leakage, not classify it.** Phase 9 must produce
   *concrete numbers*: `leakage_rate` with confidence intervals,
   `time_to_leak` distributions, and `defense_overhead` curves.
   Qualitative claims ("the attack succeeded") do not score at a
   top venue. Pre-registering the metrics in Phase 6 is a forcing
   function for this.

2. **Demonstrate defence composition.** Per Chowdhury et al. 2024
   (`literature/summaries/Chowdhury_2024_BreakingDownDefenses.md`),
   *"defenses fail under composition"* — but the converse is also
   a novelty argument: showing that the *combination* of our
   defences (per-tenant tool registries + tenant-prefixed cache
   keys + resource-path canonicalisation + mTLS) holds against the
   attack library is one of the most defensible novelty claims we
   can make.

3. **Run on real MCP servers, not only the reference pair.**
   Chen et al. 2026 observed ≈300+ runtime MCP servers; Phase 9
   should run the attack library against a public sample of these
   (or, where ethically and legally permissible, a small sample of
   local servers). Showing that the attack library generalises
   beyond our reference pair converts the paper from a "framework
   paper" to a "field study paper."

4. **Honest side-channel disclosure.** Per Dipta et al. 2024, even
   the strongest logical isolation leaves residual physical
   leakage. The paper must explicitly disclose this limitation
   (Section 11 / Discussion) rather than implicitly claiming "full
   isolation." Honest threat-model scoping is rewarded at top
   venues.

5. **Quantify cross-SDK divergence.** The Phase-1 Component-9
   finding that the Python and TypeScript MCP SDKs disagree on
   framing is novel; Phase 9 should *measure* this divergence
   quantitatively (e.g. percentage of messages framed differently
   per SDK). This is a small but defensible contribution that no
   prior work has reported.

## List of Proposed Contributions (5 numbered claims)

These are the formal, end-of-introduction style contributions that
Phase 11 will paste into `paper/sections/01_introduction.tex`.

### Contribution 1 — A complete isolation-boundary catalogue for the Model Context Protocol

- **Claim.** We present the first systematic catalogue of all
  eight MCP isolation boundaries — transport, session, namespace,
  tool, resource, memory, cache, and authentication — with a
  STRIDE-tagged attack surface per boundary and 63 forward
  ticket IDs (`A-{TRN,SES,NSP,TOL,RES,MEM,CCH,AUT}-{nnn}`)
  linking each attack surface to a concrete test case.
- **Evidence.** `docs/notes/mcp_learning/01_transport.md` …
  `09_sdks.md` (Phase 1); consolidated in
  `docs/notes/mcp_learning/00_appendix.md`; row-by-row mapping in
  `docs/02_Threat_Model.md`.
- **Delta vs. prior work.** Jing et al. 2026 propose a 5-boundary
  taxonomy for LLM-agent systems generally; ours is 8 boundaries
  specifically for MCP and includes STRIDE rows.

### Contribution 2 — A 14-concept security taxonomy with explicit MCP-boundary bindings

- **Claim.** We present a 14-concept security taxonomy — direct
  prompt injection, indirect prompt injection, jailbreaking,
  confused deputy, capability-based access control, sandbox
  escaping, side-channel leakage, cache poisoning, memory
  poisoning, namespace collision, tool squatting, resource
  traversal, request smuggling, and authentication bypass — each
  pinned to one or more MCP boundaries and each linked to a
  Phase-1 ticket ID.
- **Evidence.** `docs/notes/security_learning/01_*.md` …
  `14_*.md` (Phase 2); consolidated in
  `docs/notes/security_learning/00_index.md`; Graphviz render in
  `docs/diagrams/security_taxonomy.dot` and
  `docs/diagrams/security_taxonomy.svg`.
- **Delta vs. prior work.** No prior work pins security concepts
  to MCP-specific boundaries; OWASP LLM Top 10 v1.1 is
  LLM-application-level, not protocol-level. The closest
  architectural prior is the Capsicum capability literature,
  which is referenced conceptually in `docs/notes/security_learning/`
  but is **not protocol-bound to MCP**.

### Contribution 3 — A reproducible empirical framework that measures cross-tenant leakage in MCP deployments

- **Claim.** We present a reproducible framework that drives
  controlled multi-tenant traffic against MCP servers and
  measures `leakage_rate`, `time_to_leak`, `defense_overhead`,
  and `utility_retention` at each of the eight boundaries,
  reporting per-attack confidence intervals.
- **Evidence.** `framework/` (planned Phase 6); executed in Phase 9;
  results summarised in `analysis/tables/` and `analysis/figures/`
  (planned Phase 10).
- **Delta vs. prior work.** Chen et al. 2026 measure MCP-server
  risk in single-tenant settings only; An et al. 2026 (FlowGuard)
  detect MCP security issues via behavioural-trace correlation
  but do **not** measure cross-tenant leakage; Liu et al. 2026
  (MCPEvol-Bench) study tool evolution but not tenant isolation.

### Contribution 4 — An open attack library of ≥25 concrete attack classes covering every MCP boundary

- **Claim.** We provide an open-source attack library containing
  at least 25 concrete attack classes — covering transport framing
  attacks, session-ID collisions, namespace squatting, tool
  descriptor injection, resource path traversal, memory
  poisoning, cache-key collisions, and authentication bypass —
  each with CVSS scoring, pytest reproducer, and trace logs.
- **Evidence.** `attacks/` (planned Phase 7); per-class pytest
  runners under `attacks/<class>/test_<id>.py`.
- **Delta vs. prior work.** Wang et al. 2024 (ToolCommander)
  demonstrate tool injection in isolation; Torres et al. 2026
  demonstrate memory poisoning in isolation; Lee et al. 2026
  demonstrate mid-session tool mutation in isolation. **No prior
  work composes these into a single library with uniform pytest
  reproducibility and per-class CVSS scoring.**

### Contribution 5 — A defence-comparison study at the MCP layer

- **Claim.** We present a quantitative defence-comparison study
  at the *protocol* layer (not the OS layer) measuring the
  leakage reduction achieved by per-tenant tool registries,
  tenant-prefixed cache keys, resource-path canonicalisation,
  and mTLS — individually and in composition — against the
  Phase-7 attack library.
- **Evidence.** `mcp_servers/vulnerable/` and
  `mcp_servers/secure/` (planned Phase 8); results in
  `analysis/tables/rq4_summary.csv` (planned Phase 10).
- **Delta vs. prior work.** Dipta et al. 2024 study OS-level
  sandbox side channels; ours is protocol-level and measures
  *leakage reduction*, not *side-channel leakage*. Capsicum
  capability literature (referenced conceptually) is capability
  primitive design, not protocol-level defence evaluation.

## Verification Log

All three yes/no answers were re-verified on **2026-07-18** by
direct WebFetch of the arXiv abstract page for each cited paper:

| Paper | arXiv ID | Verification | Source |
| --- | --- | --- | --- |
| Chen et al. 2026 | 2607.11086 | VERIFIED | <https://arxiv.org/abs/2607.11086> |
| Jing et al. 2026 | 2607.12406 | VERIFIED | <https://arxiv.org/abs/2607.12406> |
| Dipta et al. 2024 | 2404.10715 | VERIFIED | <https://arxiv.org/abs/2404.10715> |

No fabricated citations. The verbatim evidence quotes above are
each attributable to the corresponding arXiv abstract page; they
are reproduced exactly as retrieved on 2026-07-18.

## Cross-Phase Traceability

- **Phase 5** (`docs/04_Attack_Taxonomy.md`) will materialise the
  STRIDE rows from Contribution 1 into attack-taxonomy tables.
- **Phase 6** (`framework/`) will pre-register the leakage
  metrics from Contribution 3.
- **Phase 7** (`attacks/`) will populate the attack library from
  Contribution 4.
- **Phase 9** (experiments) will produce the empirical numbers
  referenced in Contribution 3 and Contribution 5.
- **Phase 11** (paper) will paste the contributions list above
  into `paper/sections/01_introduction.tex` (which Phase 11 will
  create).
- **Phase 12** (reviewer simulation) will re-evaluate these
  novelty claims under hostile review.