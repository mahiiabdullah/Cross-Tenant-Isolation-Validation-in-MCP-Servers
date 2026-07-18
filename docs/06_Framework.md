# 06 — Framework

> **Phase 6 deliverable.** Design and reference implementation of
> the reproducible cross-tenant leakage measurement harness. The
> paper-ready module spec, JSON/YAML schemas, sequence diagram,
> and RunConfig schema are documented here.

## Status

All 6 prompt-mandated modules plus the Reporter exist as working
Python implementations. The end-to-end smoke test
(`experiments/scripts/run_dummy_smoke.py`) drives a dummy
attacker → dummy MCP server → dummy oracle loop and emits ≥1
JSONL event plus a Markdown + HTML report. Phase 9 will swap
the `DummyConnector` for real HTTP+SSE / stdio adapters and the
attack recipes for the Phase-7 concrete implementations.

## Module Specifications

| Module | Responsibility | Input | Output | File |
| --- | --- | --- | --- | --- |
| `Scheduler` | Drive concurrent tenants + attack queue under a `RunConfig`. | `RunConfig` | `RunSummary` (n_events, n_leakage_events, metric_results, report_paths) | `framework/scheduler/scheduler.py` |
| `PayloadGenerator` | Mutate base profiles into N unique payloads per recipe; deterministic per seed. | `AttackRecipe`, seed | list of payload strings | `framework/scheduler/payloads.py` |
| `Target MCP Connector` | Speak MCP (stdio / HTTP+SSE / streamable HTTP) per tenant; Phase 6 ships `DummyConnector`. | tenant creds, target cfg | RPC client / response dict | `framework/target/connector.py` |
| `Cross-Tenant Evaluator` (Oracle) | Classify leakage events via substring + sha256-prefix match + tag mismatch. | tool call log + tenant meta | `LeakageEvent[]` | `framework/evaluator/evaluator.py` |
| `Metrics Collector` | Aggregate per boundary / defense. | events | `MetricResult[]` | `framework/metrics/metrics.py` |
| `EventLogger` | Persist every event as JSONL. | event dict | append-only `*.jsonl` | `framework/logger/logger.py` |
| `Reporter` | Render Markdown + HTML reports from logger output. | metrics + events | `report.md`, `report.html` | `framework/reports/reporter.py` |

### Module Boundaries

```
                RunConfig (YAML)
                      │
                      ▼
                 Scheduler.run()
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
  PayloadGen     Connector    (loop over)
        │             │             │
        ▼             ▼             ▼
     payload  -->  ToolCall --> Evaluator --> LeakageEvent
                                              │
                                              ▼
                                          EventLogger
                                              │
                                              ▼
                                          compute_metrics
                                              │
                                              ▼
                                          Reporter
```

## Sequence Diagram

See `docs/diagrams/framework_sequence.md` (Mermaid source) and
`docs/diagrams/framework_sequence.svg` (rendered SVG). The
diagram covers all five prompt-required steps:

1. Framework spins up Tenant A and Tenant B.
2. Payload injected via Tenant A.
3. Tenant B's state is sampled.
4. Oracle classifies result.
5. Logger writes event.

Plus the Phase-6 extensions: metric aggregation and report
rendering.

## Data Structures (YAML schemas)

### Attack Recipe

```yaml
id: A-TRN-S               # matches docs/04_Attack_Taxonomy.md
boundary: transport       # transport | session | namespace | tool | resource | memory | cache | auth
category: spoofing        # STRIDE letter in lowercase
parameters:               # per-recipe parameters (Phase 7 will materialise)
  transport: http_sse
  replay_target: tenant-A
success_criteria:         # what the Evaluator checks for
  - type: substring
    value: "Bearer eyJ"
  - type: sha256_prefix
    length: 8
```

### Evaluation Metric

```yaml
attack_id: A-TRN-S
boundary: transport
success: true             # bool
latency_ms: 12.4          # wall-clock between call and event
payload_sha256: abc123... # sha256 of the matched excerpt
seed: 42
tenant_pair:              # ordered pair [source, sink]
  - tenant-A
  - tenant-B
```

These schemas are emitted as JSONL rows by `EventLogger.emit`
and consumed by `compute_metrics`. The
`framework/logger/logger.py:REQUIRED_KEYS` constant is the
authoritative required-key set.

## RunConfig Schema

`framework/core/config.py` defines `RunConfig` (pydantic). Load
via `RunConfig.from_yaml(path)`:

```python
from framework.core.config import RunConfig
cfg = RunConfig.from_yaml("experiments/configs/example_run.yaml")
```

The full schema:

```yaml
run:                       # RunSettings
  seed: 42
  repeats: 1
  concurrency: 4
tenants:                   # list[TenantConfig]
  - id: tenant-A
    name: Alice
    allowed_tools: [echo]
    allowed_resources: []
attacks:                   # list[AttackRef]
  - id: A-TRN-S
    parameters: {}         # free-form per-recipe
defenses:                  # Defenses
  per_tenant_tool_registry: false
  tenant_prefixed_cache_keys: false
  resource_path_canonicalisation: false
  mtls: false
target:                    # TargetConfig
  transport: dummy         # stdio | http_sse | streamable_http | dummy
  command: null
  url: null
  token: null
output:                    # OutputConfig
  log_dir: experiments/logs
  output_dir: experiments/outputs
  log_format: jsonl
```

`RunConfig` enforces at least 2 tenants (the harness requires
a `(source, sink)` pair to detect leakage).

## Metrics Definitions

| Metric | Definition |
| --- | --- |
| `leakage_rate` | fraction of call events in the bucket that have a paired leakage event (range 0–1). |
| `time_to_leak_ms` | median latency between `attack_started_at` and `leakage_detected_at` for events in the bucket. `null` if no leakage. |
| `defense_overhead_ms` | p95(latency_defended) − p95(latency_undefended). `null` if either side has no samples. |
| `utility_retention` | 1 − (errors_defended / errors_undefended), clamped to [0, 1]. Defaults to 1.0 when there are no errors on either side. |

These four metrics are the Phase-4 novelty contributions 3 and 5
pre-registered targets. They will be populated empirically in
Phase 9.

## Smoke-Test Contract (Done-When gate)

`experiments/scripts/run_dummy_smoke.py` validates the
end-to-end harness:

1. Load `experiments/configs/example_run.yaml`.
2. Instantiate `Scheduler`, `DummyConnector`, `PayloadGenerator`,
   `Evaluator`, `EventLogger`, `compute_metrics`, `Reporter`.
3. Run the loop once (2 attacks × 1 tenant pair × 1 repeat = 2
   payload injections, each producing a call + a leakage event
   when leak injection is on for the sink).
4. Assert that `experiments/logs/example_run.jsonl` contains ≥1
   event.
5. Assert that `experiments/outputs/report.md` is written.

Run with:

```bash
python experiments/scripts/run_dummy_smoke.py
```

Expected output (truncated):

```
RunSummary:
{ "n_attacks": 2, "n_tenant_pairs": 1, "n_repeats": 1,
  "n_events": 6, "n_leakage_events": 2,
  "metric_results": [...] }
Emitted 6 events to experiments/logs/example_run.jsonl
Markdown report: experiments/outputs/report.md
Smoke test PASSED
```

## Cross-References

- Threat model: `docs/02_Threat_Model.md`, `docs/04_Attack_Taxonomy.md`.
- Phase-5 attack stubs: `attacks/<boundary>/a_<boundary>_<letter>.py`
  (Phase 7 will replace `execute()` bodies).
- Phase-8 reference servers: `mcp_servers/vulnerable/` and
  `mcp_servers/secure/`.
- Phase-9 will run the Phase-6 harness end-to-end against the
  reference servers.

## Future Work

- Real HTTP+SSE / stdio transport adapters (Phase 8).
- Bounded-concurrency `asyncio.gather` driver with semaphore
  (replacing the sequential loop).
- Schema-versioned JSONL events.
- Embedding-based evaluator (Phase 7 may add; not Phase-6 scope).