# Appendix A — Data Traceability

Every number in Section 6 traces to a row in one of the four
analysis summary CSVs. This appendix documents the exact
mapping.

## RQ-1 — Baseline isolation

`paper/sections/06_evaluation.tex` Table~\ref{tab:rq1}
corresponds to `analysis/tables/rq1_summary.csv`:

| Attack | Boundary | $L_{\text{vuln}}$ | $L_{\text{secure}}$ | $t$ (paired) | $p$ | $\delta$ |
| --- | --- | --- | --- | --- | --- | --- |
| A-AUT-T | auth | 0.500 | 0.500 | 0.00 | 1.0 | 0.00 |
| A-MEM-T | memory | 0.500 | 0.500 | 0.00 | 1.0 | 0.00 |
| A-RES-T | resource | 0.500 | 0.500 | 0.00 | 1.0 | 0.00 |
| A-SES-T | session | 0.500 | 0.500 | 0.00 | 1.0 | 0.00 |
| A-CCH-T | tool | 0.500 | 0.500 | 0.00 | 1.0 | 0.00 |
| A-NSP-T | tool | 0.500 | 0.500 | 0.00 | 1.0 | 0.00 |
| A-TOL-T | tool | 0.500 | 0.500 | 0.00 | 1.0 | 0.00 |
| A-TRN-S | tool | 0.500 | 0.500 | 0.00 | 1.0 | 0.00 |

Figure~\ref{fig:rq1} is
`analysis/figures/rq1_leak_rate_by_boundary.pdf`.

## RQ-2 — Cache dominance

`paper/sections/06_evaluation.tex` Table~\ref{tab:rq2}
corresponds to `analysis/tables/rq2_summary.csv`:

| Attack | Boundary | leak count | share |
| --- | --- | --- | --- |
| A-CCH-D | tool | 465 | 0.1429 |
| A-CCH-E | tool | 465 | 0.1429 |
| A-CCH-I | tool | 465 | 0.1429 |
| A-CCH-R | tool | 465 | 0.1429 |
| A-CCH-S | tool | 465 | 0.1429 |
| A-CCH-T | tool | 465 | 0.1429 |
| A-FUZZ-001 | tool | 465 | 0.1429 |

Total: 3{,}255 leaks (100% of vulnerable-server leakage in the
RQ-2 cell). Headline: $z = 40.73$ (continuity-corrected
one-sided $z$-test, `analysis/scripts/stats.py:one_sided_z_proportion`),
$p \approx 0$.

Figure~\ref{fig:rq2} is
`analysis/figures/rq2_cache_heatmap.pdf`.

## RQ-3 — Prompt-injection residual

`paper/sections/06_evaluation.tex` Table~\ref{tab:rq3}
corresponds to `analysis/tables/rq3_summary.csv`:

| Attack | mean (ms) | p95 (ms) | $L_{\text{secure}}$ |
| --- | --- | --- | --- |
| A-TOL-001 | 0.000 | 0.000 | 0.500 |
| A-TOL-D | 0.000 | 0.000 | 0.500 |
| A-TOL-E | 0.000 | 0.000 | 0.500 |
| A-TOL-I | 0.000 | 0.000 | 0.500 |
| A-TOL-R | 0.000 | 0.000 | 0.500 |
| A-TOL-S | 0.000 | 0.000 | 0.500 |
| A-TOL-T | 0.000 | 0.000 | 0.500 |

0/7 attacks fall inside the pre-registered $[0.05, 0.30]$
corridor. Figure~\ref{fig:rq3} is
`analysis/figures/rq3_injection_latency.pdf`.

## RQ-4 — Defense composition

`paper/sections/06_evaluation.tex` Table~\ref{tab:rq4}
corresponds to `analysis/tables/rq4_summary.csv`:

| Attack | $L_{\text{none}}$ | $L_{\text{partial}}$ | $L_{\text{full}}$ | $r_i$ |
| --- | --- | --- | --- | --- |
| A-AUT-T | 0.500 | 0.186 | 0.000 | 1.000 |
| A-CCH-T | 0.500 | 0.237 | 0.000 | 1.000 |
| A-MEM-T | 0.500 | 0.194 | 0.000 | 1.000 |
| A-RES-T | 0.500 | 0.217 | 0.000 | 1.000 |
| A-TOL-T | 0.500 | 0.220 | 0.000 | 1.000 |

Sign test against the pre-registered threshold $0.5$:
$p = 0.0312$; Wilcoxon signed-rank: $p = 0.0312$; parametric
paired $t$: $p = 0$ (variance of $r_i - 0.5$ is zero because
every attack hits the $r_i = 1.0$ floor).

Figure~\ref{fig:rq4} is
`analysis/figures/rq4_defense_combo_bars.pdf`.

## How to verify

```bash
python -c "
import pandas as pd
for rq in ['rq1', 'rq2', 'rq3', 'rq4']:
    df = pd.read_csv(f'analysis/tables/{rq}_summary.csv')
    print(rq, ':', df.shape, df.columns.tolist())
"