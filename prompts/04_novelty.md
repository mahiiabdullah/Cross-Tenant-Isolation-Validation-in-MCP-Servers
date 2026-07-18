# 04 — Novelty Prompt

> **Phase 4.** Ensure the paper's contribution is publishable at a venue like
> ACM CCS. Based on the research gap found in Phase 3, critically evaluate the
> proposed research: *"Automated Cross-Tenant Isolation Validation in MCP
> Servers."*

## Definitive Answers Required

Answer the following directly (yes/no, with evidence):

1. Has anyone already built an automated red-teaming suite specifically for MCP?
2. Has the community formally modeled MCP multi-tenant trust boundaries?
3. Are there existing baseline metrics for MCP cross-tenant context leakage?

For each question, cite at most one paper or state *"no prior work found."*

## Deliverable

- **Novelty score.** Rate the contribution 1–10 and **justify** the score.
- **Strategic pivots.** A concrete list of 3–5 specific additions the project
  must include to maximize novelty at a top venue.
- **List of Proposed Contributions.** A formal, end-of-introduction style
  enumeration (typically 3–5 numbered claims).

## Template per Contribution

For each candidate contribution, fill in:

- **Claim.** What we assert.
- **Evidence.** Where in the artifact the claim is demonstrated
  (file path, figure, table, notebook cell).
- **Delta vs. prior work.** Which prior papers come closest, and how we differ.

## Targets

- Empirical measurement framework for MCP isolation.
- Taxonomy covering all eight boundaries.
- Defense comparison at the MCP layer (not OS layer).
- Open-source artifact passing a fresh-machine reproduction test.

## Done When

- [ ] All 3 questions have yes/no + evidence answers.
- [ ] A novelty score with justification is recorded in `docs/01_Research_Gap.md`.
- [ ] `paper/sections/01_introduction.tex` includes the contributions list.
