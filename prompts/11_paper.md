# 11 â€” Paper Prompt

> **Phase 11.** Draft the paper. Convert the entire research record into a
> conference-ready manuscript in `paper/`.

## Goal

Produce a single, self-contained LaTeX manuscript â€” `paper/main.tex` â€”
suitable for submission to a security venue (USENIX Security, IEEE S&P, NDSS,
or ACM CCS) that argues isolation in MCP is fundamentally broken under the
current spec and can be repaired by a layered defense blueprint.

## Section-by-Section Blueprint

| # | File                      | Job                                                                 |
|---|---------------------------|---------------------------------------------------------------------|
| 1 | `01_introduction.tex`     | motivate; state RQs; crystal-ball contribution list                 |
| 2 | `02_background.tex`       | MCP recap, isolation primer, threat-model vocabulary                 |
| 3 | `03_threat_model.tex`     | DFD + STRIDE per boundary + misuse cases (mirrors `docs/02`)         |
| 4 | `04_framework.tex`        | framework architecture (figure from `docs/diagrams/framework.svg`)  |
| 5 | `05_attacks.tex`          | attack library taxonomy + 4 macro categories (from `docs/04`)        |
| 6 | `06_evaluation.tex`       | RQ-1â€¦RQ-4 â€” text + tables + figures from `analysis/`                 |
| 7 | `07_defenses.tex`         | defense matrix + defense-combo findings                             |
| 8 | `08_related_work.tex`     | synthesise `literature/related_work.md`; contrast table              |
| 9 | `09_discussion.tex`       | limitations, ethics, generalisability, future work                   |
|10 | `10_conclusion.tex`       | one-page wrap; restate contributions; call for MCP-2 spec changes    |

## Mandatory Style Rules

1. **Citations** â€” BibLaTeX with `style=alphabetic`. Every bibliography entry
   has a one-line comment in `literature/summaries/<key>.md`.
2. **Figures** â€” `\includegraphics{paper/figures/<file>.pdf}`. Never
   reference raw paths.
3. **Tables** â€” `booktabs` style; no vertical rules; captions above for
   tables, below for figures (IEEE convention).
4. **Numbers** â€” never paste numbers without the source row from
   `analysis/tables/*.csv`.
5. **Acronyms** â€” defined on first use in `02_background.tex`.
6. **Word budget** â€” target 12 pages + unlimited references for USENIX
   template.

## Figure & Table Inventory

Reuse only what already exists:

- Figures: `paper/figures/` (pulled from `analysis/figures/`).
- Tables: `paper/tables/` (pulled from `analysis/tables/`).
- Do **not** invent new figures â€” request them from Phase-10 first.

## Abstract Skeleton (â‰¤ 200 words)

1. Context â€” MCP's promise of tool-use isolation.
2. Gap â€” no empirical study; no open attack catalogue; no defense blueprint.
3. Method â€” 25+ attacks, vulnerable vs secure MCP, 4 RQs.
4. Findings â€” top-line numbers (to be filled from `analysis/SUMMARY.md`).
5. Defense blueprint + spec-change call-to-action.

## Repo Deliverables

- `paper/main.tex` compilable with `latexmk -pdf paper/main.tex`.
- `paper/sections/01_introduction.tex` â€¦ `10_conclusion.tex`.
- `paper/references.bib` generated from `literature/bibliography.bib`.
- `paper/README.md` â€” how to build the PDF locally and via CI.

## Done When

- [ ] `latexmk -pdf paper/main.tex` exits 0 with no overfull hbox warnings.
- [ ] All 10 sections present and â‰¥ 800 words each (except conclusion).
- [ ] Every figure/table in the manuscript is present on disk in
      `paper/figures/` or `paper/tables/`.
- [ ] All RQ hypotheses have a corresponding sentence in Â§6 stating
      *accepted / rejected*.
- [ ] `paper/README.md` build instructions verified in a clean container.