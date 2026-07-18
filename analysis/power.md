# Statistical Analysis Plan — Phase 9 / Phase 10

This document pre-registers the statistical protocol that the
Phase-9 experiment runner feeds into and that Phase 10
(Analysis) will execute against `analysis/runs/<run_id>/results.csv`.

## Pre-registered choices

| Choice | Value | Rationale |
| --- | --- | --- |
| Significance level (α) | 0.05 | Conventional in security empirics. |
| Target power (1 − β) | 0.80 | Standard minimum for empirical work. |
| Primary test | Welch's t-test | Robust to unequal variances across server variants. |
| Effect size | Cliff's δ | Non-parametric; robust to non-normal latencies. |
| Multiple-testing correction | Bonferroni (within boundary) | Conservative; boundaries are the natural family. |
| Cell repetitions | n = 30 | CLT-valid per phase-9 plan. |

## Hypotheses

### RQ-1 (baseline)

- **H1**: Cross-tenant leakage rate on the **vulnerable** server ≥ 0.70.
- **H0**: Cross-tenant leakage rate on the **secure** server < 0.05.
- Reject both H1 ∩ H0 → secure reference server fails to isolate.

### RQ-2 (cache dominance)

- **H1**: Among leakage events on the vulnerable server, the
  cache boundary accounts for ≥ 50% of `event_type == leakage`.
- Test: one-sided z-test for a proportion (cache_share ≥ 0.5).

### RQ-3 (prompt injection residual)

- **H1**: Leakage rate on the **secure** server under prompt
  injection attacks is in [0.05, 0.30] (bounded residual).
- Test: one-sided t-test against 0.30 (upper bound) and 0.05
  (lower bound).

### RQ-4 (defense combo super-additivity)

- **H1**: `full` defense level drops leakage rate by ≥ 50%
  relative to `partial` (per-tenant only) at matched attack and
  iteration.
- Test: paired comparison of leakage rates per (attack,
  iteration), Welch's t-test on the difference.

## Required n per effect size

Using the standard non-parametric power formula
(Mann-Whitney U approximation) at α = 0.05 and power = 0.80:

| Effect size (Cliff's δ) | Required n per group | Notes |
| --- | --- | --- |
| 0.20 (small) | ~ 99 | Below our 30/cell; underpowered. |
| 0.35 (small-medium) | ~ 51 | Still above 30; flagged in limitations. |
| 0.50 (medium) | ~ 30 | Matches phase-9 plan. |
| 0.80 (large) | ~ 12 | Comfortably within budget. |

For headline comparisons (vulnerable vs secure) we expect
δ ≥ 0.80 because the secure server should reduce leakage to
near zero while the vulnerable server should retain it; n = 30
is more than sufficient.

For the lower-effect prompt-injection residual (RQ-3), we
treat the experiment as **exploratory** at δ = 0.35 and
**confirmatory** at δ = 0.50.

## Multiple-testing correction

Within each boundary group there are at most 6 STRIDE rows
(S/T/R/I/D/E). We apply Bonferroni at the boundary level:

```
α_adjusted = 0.05 / 6 ≈ 0.0083
```

Across boundaries we report the per-boundary adjusted p-value
but do **not** apply an additional correction — the boundaries
are independently motivated research questions.

## Phase-10 outputs

Phase 10 (notebooks in `analysis/notebooks/`) will read
`results.csv` per run and produce:

1. `analysis/statistics/rq1_effects.csv` — per-attack Welch's
   t, Cliff's δ, Bonferroni-adjusted p.
2. `analysis/figures/rq1_leakage_by_server.svg` — bar chart.
3. `analysis/statistics/power_report.md` — observed power per
   comparison (post-hoc).

## Limitations

- **n = 30** is not powered for δ = 0.20 effects; we
  characterize those comparisons as **exploratory**.
- The Phase-9 harness uses two tenants (A/B). Extending to N
  tenants would shift the cell count but is out of scope.
- The vulnerable and secure servers are reference
  implementations; production hardening would not necessarily
  match the secure baseline's residual leakage profile.
