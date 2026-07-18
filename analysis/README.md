# Phase 10 — Analysis

Statistical analysis bundle answering RQ-1…RQ-4 with reproducible code.

## Layout

```
analysis/
├── notebooks/                       # Six jupyter notebooks (01–06)
│   ├── 01_loading_and_cleaning.ipynb
│   ├── 02_rq1_baseline.ipynb
│   ├── 03_rq2_cache.ipynb
│   ├── 04_rq3_injection.ipynb
│   ├── 05_rq4_defense_combo.ipynb
│   └── 06_summary_findings.ipynb
├── scripts/                         # Reproducible Python modules
│   ├── stats.py                     # welch_t, cliffs_delta, bonferroni, cohens_d
│   ├── plots.py                     # Figure factory (PDF + PNG)
│   ├── load_runs.py                 # results.csv / meta.json loader
│   ├── run_all.py                   # Top-level driver → tables/ + figures/
│   └── build_notebooks.py           # (Re)build the 6 notebooks from scratch
├── tables/                          # CSV summaries
│   ├── rq1_summary.csv
│   ├── rq2_summary.csv
│   ├── rq3_summary.csv
│   └── rq4_summary.csv
├── figures/                         # PDF + PNG pairs
│   ├── rq1_leak_rate_by_boundary.{pdf,png}
│   ├── rq2_cache_heatmap.{pdf,png}
│   ├── rq3_injection_latency.{pdf,png}
│   └── rq4_defense_combo_bars.{pdf,png}
├── runs/<run_id>/                   # Phase-9 outputs (per RQ)
└── SUMMARY.md                       # TL;DR per RQ
```

## Reproduce End-to-End

```bash
# 1. Run all four Phase-9 experiments (30 iterations each).
for m in experiments/manifests/rq{1,2,3,4}*.yaml; do
  python -m experiments.runner --manifest "$m"
done

# 2. Generate the four tables + four figures + SUMMARY.md.
python -m analysis.scripts.run_all

# 3. (Re)build the six notebooks.
python -m analysis.scripts.build_notebooks

# 4. Execute the notebooks top-to-bottom.
jupyter nbconvert --to notebook --execute \
    analysis/notebooks/*.ipynb --inplace
```

The notebooks are committed in their executed state (with
cell outputs) so that a reviewer can `git clone && cat
analysis/notebooks/02_rq1_baseline.ipynb` and see the
results without spinning a kernel. To regenerate the
notebooks from scratch (e.g.\ after editing the underlying
Python modules), run `python -m
analysis.scripts.build_notebooks` and then re-execute step 4.


## Statistical Protocol

See `analysis/power.md` for the pre-registered analysis plan
(α = 0.05, power = 0.80, Welch's t, Cliff's δ, Bonferroni
within boundary, n = 30/cell).

## Notebooks

| # | Topic | RQ | Output |
|---|-------|----|----|
| 01 | Loading + schema check | — | Prints row count |
| 02 | Baseline isolation (vulnerable vs secure) | RQ-1 | `tables/rq1_summary.csv`, `figures/rq1_leak_rate_by_boundary.{pdf,png}` |
| 03 | Cache dominance on vulnerable server | RQ-2 | `tables/rq2_summary.csv`, `figures/rq2_cache_heatmap.{pdf,png}` |
| 04 | Prompt-injection residual on secure | RQ-3 | `tables/rq3_summary.csv`, `figures/rq3_injection_latency.{pdf,png}` |
| 05 | Defense-combo super-additivity | RQ-4 | `tables/rq4_summary.csv`, `figures/rq4_defense_combo_bars.{pdf,png}` |
| 06 | Summary findings (reused in paper §06) | — | Echoes `SUMMARY.md` |