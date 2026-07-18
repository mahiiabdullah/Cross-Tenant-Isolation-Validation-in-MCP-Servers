# 09 â€” Experiments Prompt

> **Phase 9.** Run the implemented framework against the vulnerable and secure
> servers across all Phase-7 attacks â€” reproducibly.

## Goal

Produce a structured experiment suite whose raw outputs (CSV / NDJSON) feed
Phase-10 analysis and ultimately Phase-11 tables/figures. Every run is a
re-runnable YAML manifest.

## Research Questions â†’ Hypotheses

| RQ    | Hypothesis                                                                                |
|-------|-------------------------------------------------------------------------------------------|
| RQ-1  | H1: vulnerable MCP fails â‰¥ 70 % of cross-tenant isolation attacks; secure fails < 5 %.    |
| RQ-2  | H2: cache-boundary attacks dominate leak volume when caching is enabled.                  |
| RQ-3  | H3: prompt-injection attacks yield bounded but non-zero leaks even on secure builds.      |
| RQ-4  | H4: defense combinations interact super-additively when ordered along the trust chain.    |

## Experimental Variables

- **Independent** â€” attack id, server variant (`vulnerable`/`secure`),
  defense configuration (`none`/`per-tenant`/`full`).
- **Dependent** â€” leak rate, latency p50/p95, CPU/RAM peak,
  false-positive rate of anomaly detector.
- **Controlled** â€” dataset version, model version (if LLM-mediated),
  seed, container limits.

## Manifest Schema (`experiments/manifests/*.yaml`)

```yaml
run_id: exp-2025-04-12-rq1
seed: 42
servers:
  - name: vulnerable-baseline
    image: mcp-server:vulnerable@v0.1
    flags: { symlinks: on, shared_transport: on }
  - name: secure-reference
    image: mcp-server:secure@v0.1
attacks:
  - id: A-TRN-001
    iterations: 50
  - id: A-SES-002
    iterations: 50
metrics:
  collect: [leak_rate, latency_p50, latency_p95]
output:
  dir: analysis/runs/exp-2025-04-12-rq1
  format: [ndjson, csv]
```

## Statistical Protocol

- â‰¥ 30 iterations per (attack Ã— server Ã— defense) cell â†’ CLT-valid means.
- Welch's *t*-test for pairwise server variants; Bonferroni-correct across
  attacks in the same boundary.
- Effect size reported as Cliff's Î´.
- Pre-registered power analysis in `analysis/power.md` (target power = 0.8,
  Î± = 0.05).

## Repo Deliverables

- `experiments/manifests/rq1_baseline.yaml`
- `experiments/manifests/rq2_cache.yaml`
- `experiments/manifests/rq3_injection.yaml`
- `experiments/manifests/rq4_defense_combo.yaml`
- `experiments/runner.py` â€” driver that materialises a manifest into
  `analysis/runs/<run_id>/`.
- `experiments/README.md` â€” how to launch on a single host or via Docker
  Compose.

## Done When

- [ ] Four RQ manifests committed.
- [ ] `python -m experiments.runner --manifest experiments/manifests/rq1_baseline.yaml`
      produces `analysis/runs/<run_id>/results.{ndjson,csv}`.
- [ ] Each manifest runs end-to-end without manual intervention.
- [ ] Run metadata (`run_id`, `commit_sha`, `seed`, `duration_s`) recorded in
      `analysis/runs/<run_id>/meta.json`.
- [ ] Logs rotated and archived under the same run directory.