# Phase 9 — Experiments

This directory contains the Phase-9 experiment manifests, the
runner driver, and the per-RQ outputs that feed Phase 10
(Analysis).

## Layout

```
experiments/
├── manifests/
│   ├── demo.yaml              # Phase-8 demo (kept for backwards compat)
│   ├── rq1_baseline.yaml      # RQ-1: vulnerable vs secure cross-tenant
│   ├── rq2_cache.yaml         # RQ-2: cache-boundary dominance
│   ├── rq3_injection.yaml     # RQ-3: prompt-injection residual risk
│   └── rq4_defense_combo.yaml # RQ-4: defense-combo interaction
├── runner.py                  # Phase-9 driver (this file's sibling)
└── README.md                  # this file
```

## Running a single RQ

```bash
python -m experiments.runner --manifest experiments/manifests/rq1_baseline.yaml
```

The runner writes its outputs into
`analysis/runs/<run_id>/`:

```
analysis/runs/<run_id>/
├── cells/
│   ├── vulnerable__none/      # one cell of (server, defense)
│   │   ├── events.jsonl       # raw events emitted by the CLI
│   │   ├── manifest.yaml      # derived RunConfig used by the CLI
│   │   ├── report.md          # per-cell report
│   │   └── report.html
│   └── secure__none/
├── results.ndjson             # aggregated events (one per row)
├── results.csv                # flattened table view
└── meta.json                  # run_id, commit_sha, seed, duration_s
```

## Running the full matrix

```bash
for m in experiments/manifests/rq{1,2,3,4}*.yaml; do
  python -m experiments.runner --manifest "$m"
done
```

## Design Notes

- **Reuse the Phase-8 CLI**: the runner spawns
  `python framework/cli.py run <derived_manifest>` once per
  `(server, defense)` cell.
- **Iterations**: the CLI flag `--iterations N` replays the
  scheduler N times with `seed + offset + i` per iteration.
  Each cell gets a unique seed range so the full matrix is
  reproducible end to end.
- **Defense levels**: the runner maps the manifest's
  `defenses` strings (`none` / `partial` (alias `per_tenant`) /
  `full`) onto the Phase-6 `Defenses` block before invoking
  the CLI.

## Statistical Protocol

See [`../../analysis/power.md`](../../analysis/power.md) for the
pre-registered power analysis, hypothesis tests, and effect-size
estimates. Phase 10 will read `results.csv` and compute the
Welch's t-test, Bonferroni correction, and Cliff's δ metrics.
