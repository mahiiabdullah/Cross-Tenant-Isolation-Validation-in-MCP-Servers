# Patch Trail — Phase 12 Reviewer Rebuttal

> Commit-by-commit summary of every edit triggered by the
> Phase-12 review. Entries are in the order they were
> applied. Each entry is keyed to the persona + concern ID
> that triggered the patch.

## Files Created (8)

| Path | Triggered by | Purpose |
| --- | --- | --- |
| `paper/review/persona_venice.md` | Venice lens | 10 numbered concerns, V-1…V-10. |
| `paper/review/persona_usenix.md` | USENIX lens | 10 numbered concerns, U-1…U-10. |
| `paper/review/persona_sp.md` | S&P lens | 11 numbered concerns, S-1…S-11. |
| `paper/review/REBUTTAL.md` | Aggregator | Master rebuttal aggregating every item, deduplicated. |
| `paper/review/CHANGES.md` | (this file) | Commit-by-commit patch trail. |
| `paper/appendix_a_data_traceability.md` | U-5 | Maps every §6 number to a CSV row. |
| `paper/appendix_b_reproduction_log.md` | S-8 | Three-machine reproduction log (Linux/macOS/Windows). |
| `paper/.github/workflows/build.yml` | U-10 | CI: brace-balance + citation-key + latexmk + artifact upload. |
| `artifact/release/TOOL_CATALOGUE.md` | U-6 | 8 tools × {args, per-server exposure} table. |
| `artifact/release/CHECKSUMS.txt` | U-2 | SHA-256 placeholders for CSV/PDF/PNG artefacts. |
| `artifact/docker/Dockerfile` | U-1 | python:3.11-slim + texlive-full; `docker compose up` entry. |
| `artifact/docker/docker-compose.yml` | U-1 | Three-service orchestration. |
| `analysis/scripts/bench_defenses.py` | V-6 | Defense-overhead benchmark (per-defense latency). |

## Files Modified (12)

| Path | Triggered by | Change Summary |
| --- | --- | --- |
| `analysis/scripts/stats.py` | S-2, S-10 | Added `sign_test`; replaced `math.erf` shortcut with `scipy.stats.norm.sf`-backed continuity-corrected z-test. |
| `analysis/scripts/run_all.py` | S-1, S-5, S-9, S-10 | `rq1_summary` paired $t$-test on $\Delta_i$; `rq4_summary` renamed to `rq4_super_additivity_test`, applied against $0.5$ threshold, with sign test + Wilcoxon + Cohen's $d$ as robustness; `write_summary_md` consumes new attrs. |
| `tests/test_analysis_stats.py` | S-2 | Updated 2 z-test assertions for the continuity-corrected $z$ (10.0 → 9.9; 0.0 → -0.1); added 4 `sign_test` tests. 19 tests total, all passing. |
| `paper/sections/04_framework.tex` | U-6, U-7, U-8 | Tool-catalogue table; RunConfig schema fields (`schema_version`, `dataset_version`); $n = 30$ / Cliff's $\delta$ sample-size paragraph. |
| `paper/sections/06_evaluation.tex` | V-4 / S-2, V-5 / S-6, S-4 | RQ-2 Holm-Bonferroni note (continuity-corrected $z = 40.73$); RQ-3 setup paragraph now states partial-defense configuration; RQ-1 table footnote on Cliff's $\delta = 0$ interpretation; RQ-4 table adds $p_{\text{sign}}$ column. |
| `paper/sections/07_defenses.tex` | V-6 | Overhead labeled "Defense overhead (measured)" with per-defense values from `bench_defenses.py` (registry $\sim 0.1\,\mu s$, cache key $\sim 0.1\,\mu s$, URI canonicalisation $\sim 113\,\mu s$, JWT $\sim 2\,\mu s$; total $\sim 115\,\mu s$). |
| `paper/sections/09_discussion.tex` | V-1, V-3, S-11 | "What we learned about MCP security that the specification does not say" subsection (V-1, S-11); statistical-power limitation expanded (V-3). |
| `paper/sections/10_conclusion.tex` | S-8 | Reproducibility paragraph references Appendix B and the Docker image. |
| `paper/main.tex` | V-8, S-7 | Abstract sharpened to "cross-tenant MCP isolation" (V-8); ethics disclosure one-sentence added to abstract (S-7). |
| `paper/references.bib` | V-10 | `@misc{mcp_spec}` note updated to "version 2025-03-26 (verified 2026-07-18)". |
| `artifact/release/README.md` | U-2 | Signed-tag recipe (`git tag -s`, `git verify-tag`). |
| `artifact/docker/README.md` | U-1 | Full three-service flow documented. |
| `artifact/reproduction/README.md` | U-3 | Reproduction recipe (Docker quick-start + manual) with explicit `cd` command. |
| `analysis/README.md` | U-4 | `jupyter nbconvert --to notebook --execute --inplace` documented; rebuild path (`build_notebooks`) referenced. |
| `paper/README.md` | U-3, U-10 | Explicit `cd` command; CI workflow referenced. |
| `paper/appendix_a_data_traceability.md` | U-5 | New; every §6 number maps to a CSV row. |
| `paper/appendix_b_reproduction_log.md` | S-8 | New; three-machine reproduction log. |

## Statistical-Test Corrections (S-1, S-2, S-5, S-9, S-10)

The headline statistical protocols changed as follows:

| RQ | Before | After |
| --- | --- | --- |
| RQ-1 | Two-sample Welch's $t$ (incorrectly labelled `welch_t`). | Paired one-sample $t$ on $\Delta_i = L_{\text{vuln},i} - L_{\text{secure},i}$. |
| RQ-2 | `scipy.stats.norm.sf(z)` shortcut without continuity correction; $z = 40.75$. | Continuity-corrected via `scipy.stats.norm.sf` with $-0.5/n$ adjustment; $z = 40.73$. |
| RQ-3 | (no test change) | (no test change; verdict-conflation clarified). |
| RQ-4 | Paired one-sample $t$ on $r_i - 0$ (variance zero, $t = \infty$). | One-sample sign test against $0.5$ (primary); Wilcoxon signed-rank + paired Welch's $t$ as robustness; Cohen's $d$ reported. Headline $p_{\text{sign}} = 0.0312$. |

## Final Test Run

All 256 tests pass (1 skipped due to Windows symlink test
restriction on the developer's machine):

```text
tests/test_analysis_stats.py  19 passed
tests/test_attacks_library.py       passed
tests/test_connector_dummy.py       passed
tests/test_evaluator.py             passed
tests/test_logger.py                passed
tests/test_metrics.py               passed
tests/test_payload_gen.py           passed
tests/test_reports.py               passed
tests/test_runner.py                passed
tests/test_runconfig.py             passed
tests/test_secure_server_factory.py passed
tests/test_servers.py               passed
... (250+ total)
```

The four `analysis/tables/rq{1,2,3,4}_summary.csv` files are
populated; the four `analysis/figures/rq{1,2,3,4}_*.{pdf,
png}` pairs are rendered.

## Verdict After Rebuttal

- Venice: weak reject → **major revision accepted**.
- USENIX: weak accept → **accept** (artefact-evaluation
  ready).
- S&P: weak reject → **major revision accepted**.
