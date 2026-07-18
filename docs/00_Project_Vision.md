# 00 — Project Vision

> Status: Draft. Living document.

## Motivation

The Model Context Protocol (MCP) lets language models invoke external tools and resources across process boundaries. As MCP deployments become **multi-tenant** (one MCP server serving multiple users, agents, or organizations), the question of **isolation** becomes central:

- Can tenant A observe tenant B's tool calls, results, prompts, or cached state?
- Can a malicious prompt cause a server to leak data across tenant boundaries?
- Are transport, session, namespace, tool, resource, and memory boundaries actually enforced?

## Research Questions

1. **Mapping.** Which isolation boundaries does MCP define, and which are merely implied?
2. **Measurement.** Can cross-tenant leakage be empirically detected and quantified?
3. **Attack.** Which attack patterns reliably break isolation, and under what conditions?
4. **Defense.** What defense strategies reduce leakage while preserving utility and performance?

## Scope

| In Scope | Out of Scope |
| --- | --- |
| Multi-tenant MCP servers | Single-tenant desktop setups |
| Prompt-, tool-, resource-, memory-, cache-, session-, transport-layer attacks | Attacks against the underlying LLM provider's training |
| Reproducible empirical evaluation | Production incident forensics |
| Defenses deployable at the MCP layer | OS-level sandboxing as the only mitigation |

## Deliverables

- Threat model and attack taxonomy (`docs/02_Threat_Model.md`, `docs/04_Attack_Taxonomy.md`).
- Isolation measurement framework (`framework/`).
- Reference attack library (`attacks/`).
- Reference MCP servers: vulnerable and hardened (`mcp_servers/`).
- Experiment harness and statistical analysis (`experiments/`, `analysis/`).
- Peer-reviewable paper and artifact (`paper/`, `artifact/`).

## Success Criteria

- At least 5 isolation boundaries empirically evaluated.
- At least 10 reproducible attack scenarios with measurable cross-tenant leakage.
- At least 3 defense strategies benchmarked against the attack library.
- Artifact passes a fresh-machine reproduction test.