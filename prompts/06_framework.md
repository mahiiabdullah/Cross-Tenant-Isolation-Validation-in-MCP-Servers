# 06 — Framework Prompt

> **Phase 6.** Design the software that will be built. Architect the automated
> multi-agent red-teaming framework required to execute the Phase-5 threat
> model against an MCP server.

## Goal

A reusable, reproducible harness that:

- Spins up multiple tenants against one MCP server.
- Mutates and injects attack payloads.
- Detects cross-tenant leakage via an oracle.
- Emits structured events + metrics.

## Deliverable 1 — Module Specifications

For each module, list responsibilities, inputs, outputs, and dependencies:

| Module | Responsibility | Input | Output |
| --- | --- | --- | --- |
| `Scheduler` | Drive concurrent tenants + attack queue | `RunConfig` | per-call events |
| `Attack Payload Generator` | Mutate base profiles into N unique payloads | attack recipe | payload queue |
| `Target MCP Connector` | Speak MCP (stdio/SSE) per tenant | tenant creds | RPC client |
| `Cross-Tenant Evaluator` (Oracle) | Classify leakage events | tool call log + tenant meta | `LeakageEvent`[] |
| `Metrics Collector` | Aggregate per boundary / defense | events | `MetricResult` |
| `Logger` | Persist every event as JSONL | events | `experiments/logs/*.jsonl` |

## Deliverable 2 — Sequence Diagram

Mermaid.js sequence diagram showing:

1. Framework spins up Tenant A and Tenant B.
2. Payload injected via Tenant A.
3. Tenant B's state is sampled.
4. Oracle classifies result.
5. Logger writes event.

Save the rendered SVG to `docs/diagrams/framework_sequence.svg`.

## Deliverable 3 — Data Structures

Define JSON/YAML schemas for:

- **Attack Recipe.** `id`, `boundary`, `category`, `parameters`, `success_criteria`.
- **Evaluation Metric.** `attack_id`, `boundary`, `success(bool)`,
  `latency_ms`, `payload_sha256`, `seed`, `tenant_pair`.

## Repo Deliverables

- Concrete `RunConfig` schema in `framework/core/config.py`.
- Working `Scheduler` driving concurrent tenants.
- Working `Evaluator` emitting `LeakageEvent`s.
- Working `EventLogger` writing JSONL to `experiments/logs/`.
- Working `Reporter` producing HTML + Markdown.

## Done When

- [ ] All 6 module stubs exist under `framework/`.
- [ ] `framework.core.config.RunConfig` validates a YAML config.
- [ ] A dummy attacker → dummy MCP server → dummy oracle loop logs one event
      end-to-end without exceptions.