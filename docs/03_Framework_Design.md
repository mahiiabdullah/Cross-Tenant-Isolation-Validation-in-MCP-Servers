# 03 — Framework Design

> TBD: detailed design of the isolation measurement framework.

## Goals

- **Replayable.** Given a config + dataset, produce identical results.
- **Tenant-aware.** First-class notion of `tenant_id` across scheduler, evaluator, logger.
- **Multi-boundary.** Cover transport, session, namespace, tool, resource, memory, cache, auth.
- **Pluggable.** Add new attacks/defenses/metrics without changing the core.

## Architecture

```
                ┌──────────────────────────────┐
                │   Experiment Driver (CLI)    │
                └────────────┬─────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │Scheduler │   │Evaluator │   │ Metrics  │
        └────┬─────┘   └────┬─────┘   └────┬─────┘
             │              │              │
             ▼              ▼              ▼
        ┌──────────────────────────────────────┐
        │           Core (Tenants, Sessions)   │
        └──────────────────────────────────────┘
                             │
                             ▼
                       ┌───────────┐
                       │  Logger   │
                       └───────────┘
```

### Modules (`framework/`)

- `core/` — Domain types: `Tenant`, `Session`, `Tool`, `Resource`, `Boundary`, `LeakageEvent`.
- `scheduler/` — Drives concurrent tenant traffic, schedules attacks.
- `evaluator/` — Detects whether an attack succeeded.
- `metrics/` — Computes precision/recall/F1, leakage rate, latency overhead.
- `logger/` — Structured event log (JSONL) for offline analysis.
- `reports/` — Renders HTML/Markdown/LaTeX reports from logger output.
- `utils/` — Shared helpers (ids, hashing, time, concurrency primitives).

## Configuration

- `experiments/configs/*.yaml` declares tenants, attacks, defenses, metrics, run limits.
- The framework hydrates a `RunConfig` and emits a single `RunResult` containing per-attack, per-defense outcomes.

## Metrics (planned)

- **Leakage rate** — fraction of attack runs that surface cross-tenant data.
- **Time-to-leak** — wall-clock from attack start to first detected leakage event.
- **Defense overhead** — p50/p95 latency under defense vs. baseline.
- **Utility retention** — fraction of legitimate requests still succeeding.

## Reproducibility

- Deterministic RNG seeded per run.
- Pinned dependency versions in `requirements.txt`.
- Docker images in `artifact/docker/` for byte-identical reproduction.