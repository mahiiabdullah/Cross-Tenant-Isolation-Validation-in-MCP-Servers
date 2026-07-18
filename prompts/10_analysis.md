# 10 â€” Analysis Prompt

> **Phase 10.** Turn raw experiment outputs into statistically defensible
> findings, visualisations, and the master result tables that the paper
> ingests.

## Goal

Produce a self-contained analysis bundle (notebooks + scripts + tables +
figures) that answers RQ-1â€¦RQ-4 with reproducible code.

## Output Bundle

```text
analysis/
â”œâ”€â”€ notebooks/
â”‚   â”œâ”€â”€ 01_loading_and_cleaning.ipynb
â”‚   â”œâ”€â”€ 02_rq1_baseline.ipynb
â”‚   â”œâ”€â”€ 03_rq2_cache.ipynb
â”‚   â”œâ”€â”€ 04_rq3_injection.ipynb
â”‚   â”œâ”€â”€ 05_rq4_defense_combo.ipynb
â”‚   â””â”€â”€ 06_summary_findings.ipynb
â”œâ”€â”€ scripts/
â”‚   â”œâ”€â”€ stats.py           # Welch's t, Cliff's Î´, Bonferroni helpers
â”‚   â””â”€â”€ plots.py           # Matplotlib / seaborn figure factory
â”œâ”€â”€ runs/<run_id>/
â”‚   â”œâ”€â”€ results.ndjson
â”‚   â”œâ”€â”€ results.csv
â”‚   â””â”€â”€ meta.json
â”œâ”€â”€ tables/
â”‚   â”œâ”€â”€ rq1_summary.csv
â”‚   â”œâ”€â”€ rq2_summary.csv
â”‚   â”œâ”€â”€ rq3_summary.csv
â”‚   â””â”€â”€ rq4_summary.csv
â””â”€â”€ figures/
    â”œâ”€â”€ rq1_leak_rate_by_boundary.{pdf,png}
    â”œâ”€â”€ rq2_cache_heatmap.{pdf,png}
    â”œâ”€â”€ rq3_injection_latency.{pdf,png}
    â””â”€â”€ rq4_defense_combo_bars.{pdf,png}
```

## Notebook Conventions

1. **First cell = provenance** â€” run_id, commit_sha, dataset version, seed.
2. **Second cell = load** â€” read `runs/<run_id>/results.ndjson`; assert
   schema; report row count.
3. **Analysis cells** â€” one per research question, each producing exactly one
   CSV in `tables/` and one figure in `figures/`.
4. **Last cell = summary** â€” markdown bullet list of findings + caveats;
   this is the text reused verbatim in `paper/sections/06_evaluation.tex`.

## Statistics Helper Contract (`analysis/scripts/stats.py`)

```python
def welch_t(a: list[float], b: list[float]) -> tuple[float, float]: ...
def cliffs_delta(a: list[float], b: list[float]) -> float: ...
def bonferroni(pvals: list[float]) -> list[float]: ...
def cohens_d(a: list[float], b: list[float]) -> float: ...
```

## Figure Specs

| Figure                       | Type        | X-axis           | Y-axis          | Hue      |
|------------------------------|-------------|------------------|-----------------|----------|
| `rq1_leak_rate_by_*.png`     | grouped bar | Boundary         | Leak rate [%]   | Server   |
| `rq2_cache_heatmap.png`      | heatmap     | Attack Ã— Defense | Leak count      | â€”        |
| `rq3_injection_latency.png`  | box+strip   | Attack           | Latency ms      | Server   |
| `rq4_defense_combo_bars.png` | stacked bar | Defense combo    | Leak reduction  | Boundary |

All figures exported as both PDF (paper) and PNG (slide deck).

## Repo Deliverables

- All notebooks executed top-to-bottom, kernels saved.
- `analysis/README.md` â€” table of contents, how to re-run.
- `analysis/SUMMARY.md` â€” one-paragraph TL;DR per RQ for the paper's
  abstract and intro.

## Done When

- [ ] `jupyter nbconvert --to notebook --execute analysis/notebooks/*.ipynb`
      exits 0.
- [ ] CSV tables in `analysis/tables/` match the cell counts in
      `paper/sections/06_evaluation.tex` draft.
- [ ] Figures in `analysis/figures/` referenced (by relative path) from the
      same `.tex` file.
- [ ] Statistical significance flagged in every table footnote (asterisk /
      dagger).