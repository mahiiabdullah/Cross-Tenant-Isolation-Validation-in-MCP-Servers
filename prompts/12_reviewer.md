# 12 â€” Reviewer Prompt

> **Phase 12.** Simulate a hostile, three-persona peer review and rebut every
> critique. Convert the review back into revisions *before* the real
> submission is sent.

## Goal

Catch, in private, every weakness a tough committee would notice and patch
the manuscript until a fresh round of three-persona review returns zero
blockers.

## Three Reviewer Personas

| Persona                    | Stance                                                       | Lens                                                |
|----------------------------|--------------------------------------------------------------|-----------------------------------------------------|
| **Venice (Adversarial)**   | Reject unless contribution is novel and methodology airtight  | novelty, threat-model completeness, soundness       |
| **USENIX Pragmatist**      | Will publish if a reader can replicate in two evenings        | reproducibility, artefact availability, clarity      |
| **S&P Rigorist**           | Statistical and ethical rigour above all                     | stats methodology, ethics disclosure, baselines      |

For each persona, write a numbered, â‰¥ 8-item list of concerns. Address every
numbered item with one of:

- **Fixed** â€” describe the patch and link the commit/diff.
- **Partial** â€” describe what was fixed and what remains, with a timeline.
- **Declined** â€” give a one-paragraph rebuttal grounded in evidence.

## Review Surface

Run the three reviews against:

1. `paper/main.tex` (full compile).
2. `docs/02_Threat_Model.md` + `docs/03_Framework_Design.md`.
3. `analysis/SUMMARY.md` + every figure in `analysis/figures/`.
4. `artifact/` â€” completeness of the open-science bundle.

## Self-Rebuttal Template

For every reviewer item:

```text
[#] Reviewer: "<quote>"
    Concern:    <one-line summary>
    Evidence:   <file:line or table:cell>
    Action:     <fixed | partial | declined>
    Patch:      <commit / file:line rewritten>
    Justified:  <why this is sufficient or why decline>
```

## Repo Deliverables

- `paper/review/persona_venice.md`
- `paper/review/persona_usenix.md`
- `paper/review/persona_sp.md`
- `paper/review/REBUTTAL.md` â€” master rebuttal document that aggregates
  every item across personas, deduplicated.
- `paper/review/CHANGES.md` â€” commit-by-commit changelog of edits triggered
  by the reviews.

## Done When

- [ ] Each persona file has â‰¥ 8 actionable items.
- [ ] `REBUTTAL.md` cross-references every claim to either a code cell, a
      table cell, or a figure panel.
- [ ] Re-running the three personas on the patched manuscript produces zero
      new *blocker*-level items.
- [ ] `paper/review/CHANGES.md` shows the manuscript is **strictly** stronger
      than the pre-review version (per-page claim density, statistical
      hedges, reproducible commands).
- [ ] All reviewer-driven edits are reflected back into the relevant
      `paper/sections/*.tex` files.