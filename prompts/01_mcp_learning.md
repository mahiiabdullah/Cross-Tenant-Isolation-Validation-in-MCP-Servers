# 01 — MCP Learning Prompt

> **Phase 1.** Force the assistant to map the exact specifications and attack
> surfaces of the Model Context Protocol *before* any methodology is discussed.

## Goal

Produce a comprehensive, structurally rigid technical knowledge base of MCP
suitable for inclusion as a paper appendix. *Do not summarize — deconstruct.*

## Output Structure (per component)

- **(A) Purpose.** One-paragraph formal statement.
- **(B) Internal Workflow.** Message types, lifecycle, ordering constraints.
- **(C) Data Flow.** Inputs/outputs, JSON-RPC framing, payload schemas.
- **(D) Inherent Security Implications.** Defaults, trust assumptions, footguns.
- **(E) Theoretical Attack Surface.** Concrete attacker-controlled inputs.

## Components to Analyze

1. **Transport layers.** `stdio` vs. `SSE/HTTP` — framing, multiplexing, reconnection.
2. **Tools & tool execution routing.** Registration, discovery, dispatch, error handling.
3. **Resources & resource templates.** URI schemes, listing, subscription, pagination.
4. **Prompts & context injection mechanisms.** Template rendering, parameter binding.
5. **Authentication & authorization boundaries.** Tokens, scopes, capability negotiation.
6. **Session lifecycle & state management.** Init / ping / shutdown, cancellation, deadlines.
7. **Context management & memory persistence.** Server-side caches, embeddings, history.
8. **Multi-client to single-server concurrency.** Fan-in patterns, queueing, locks.
9. **Official SDK implementation nuances.** Python and TypeScript SDKs — divergences and defaults.

## Quality Bar

- Cite specification section numbers where possible. If a number is unknown,
  state *"spec section requires empirical verification."*
- Use ` ```json ` code fences for protocol message examples.
- Every (E) attack surface must reference a future ticket in
  `docs/04_Attack_Taxonomy.md`.

## Repo Deliverables

- One `.md` per component under `docs/notes/mcp_learning/`.
- Updated boundary table in `docs/02_Threat_Model.md`.
- Consolidated appendix `docs/notes/mcp_learning/00_appendix.md`.

## Done When

- [ ] All 9 components have A–E sections.
- [ ] Appendix renders with no `TBD` markers.
- [ ] Every attack surface in (E) has a ticket ID linking into Phase 5.
