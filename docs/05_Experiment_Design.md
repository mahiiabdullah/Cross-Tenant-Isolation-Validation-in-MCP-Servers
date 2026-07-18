# 05 — Experiment Design

> TBD: experiment matrix, sampling plan, statistical tests.

## Variables

- **Independent.** Attack class, defense strategy, tenant count, concurrency.
- **Dependent.** Leakage rate, time-to-leak, defense overhead, utility retention.
- **Controlled.** MCP server implementation (vulnerable vs. secure), transport, dataset.

## Experiment Matrix (placeholder)

| Exp ID | Server | Attacks | Defenses | Tenants | Repeats |
| --- | --- | --- | --- | --- | --- |
| E1 | vulnerable | baseline (none) | none | 3 | 30 |
| E2 | vulnerable | full library | none | 3 | 30 |
| E3 | secure | full library | full | 3 | 30 |
| E4 | vulnerable | full library | per-defense | 3 | 30 |
| E5 | secure | fuzzing suite | full | 5 | 10 |

## Statistical Plan

- Binomial CIs on leakage rates (Wilson interval).
- Mann–Whitney U for latency overhead comparisons.
- Holm–Bonferroni correction across multiple attacks/defenses.

See `analysis/notebooks/` (planned) for executable notebooks.