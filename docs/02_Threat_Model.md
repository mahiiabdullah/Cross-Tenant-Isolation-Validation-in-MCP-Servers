# 02 — Threat Model

> **Phase 1 + Phase 5 deliverable.** Hybrid STRIDE + trust-boundary
> enumeration for MCP. Phase 1 catalogued the 8 boundaries with 63
> forward ticket IDs; Phase 5 materialises them as STRIDE rows +
> misuse cases in `docs/04_Attack_Taxonomy.md`.

## System Definition

### Assets

- **Data.** Tenant-owned documents, embeddings, conversation
  history, tool outputs, cached prompts, resource blobs.
- **Credentials.** Bearer tokens, mTLS client certificates,
  refresh tokens, session IDs.
- **Sessions.** Per-connection state: resolved principal,
  per-session caches, in-flight cancellation tokens, SSE event
  queues.
- **Embeddings.** Server-side vector representations of prior
  prompts and tool outputs (long-lived PII risk).
- **Tool outputs.** Cached or in-flight results from
  `tools/call` invocations.
- **Capability registries.** Server-side tool / resource /
  prompt catalogues and the descriptors they expose.

### Actors

- **Honest Tenant.** A user with legitimate access to a subset
  of MCP tools/resources.
- **Malicious Tenant.** A user who attempts to access data or
  capabilities outside their authorized scope.
- **Compromised Agent.** An MCP client whose prompt context is
  partially controlled by an attacker.
- **Malicious MCP Server.** A server that misbehaves across
  tenants.
- **Network Adversary.** Passive observer or active MITM on the
  transport channel.
- **Server Admin.** Operator with host-level access; trusted
  in Phase-9 deployment but not in the protocol-level threat
  model.

### Trust Boundaries

| Boundary | Definition | Trust Assumption | Phase-1 surface refs |
| --- | --- | --- | --- |
| Transport | stdio / HTTP / SSE channel between client and server | Channel may be hostile | `docs/notes/mcp_learning/01_transport.md` §B–E (tickets `A-TRN-001`–`A-TRN-009`) |
| Session | Per-connection state on the server | Sessions must not leak across tenants | `docs/notes/mcp_learning/06_sessions.md` §B–E (tickets `A-SES-001`–`A-SES-009`) |
| Namespace | Tool/resource naming and discovery | Names must be tenant-scoped | `docs/notes/mcp_learning/02_tools_routing.md` §E, `04_prompts_context.md` §E, `09_sdks.md` §E (tickets `A-NSP-001`–`A-NSP-007`) |
| Tool | Tool invocation and result delivery | Inputs/outputs must not leak | `docs/notes/mcp_learning/02_tools_routing.md` §B–E, `04_prompts_context.md` §C–E, `09_sdks.md` §E (tickets `A-TOL-001`–`A-TOL-010`) |
| Resource | File/blob/URI access via MCP resources | Access control enforced per tenant | `docs/notes/mcp_learning/03_resources.md` §B–E, `04_prompts_context.md` §C (tickets `A-RES-001`–`A-RES-007`) |
| Memory | Server-side conversation memory / cache | Memory must be tenant-scoped | `docs/notes/mcp_learning/07_context_memory.md` §B–E, `08_concurrency.md` §E (tickets `A-MEM-001`–`A-MEM-008`) |
| Cache | Cached tool outputs / embeddings | Cache keys and values must be tenant-scoped | `docs/notes/mcp_learning/07_context_memory.md` §B–E, `02_tools_routing.md` §E (tickets `A-CCH-001`–`A-CCH-005`) |
| Auth | Token / scope verification | Tokens must be unforgeable and scoped | `docs/notes/mcp_learning/05_auth.md` §B–E, `04_prompts_context.md` §E, `06_sessions.md` §E (tickets `A-AUT-001`–`A-AUT-008`) |

## Attacker Capabilities (in scope)

The following are assumed in scope for Phase 9's evaluation
harness:

- The attacker has execution rights in **Tenant A** (one
  legitimate tenant account).
- The attacker can **register tools, read public resources,
  and call any public method** on the server.
- The attacker can **inject content** via prompt, resource, or
  tool result.
- The attacker can observe **timing and error responses** from
  the server.
- The attacker can run **multiple concurrent connections**
  simultaneously (subject to per-tenant rate limits, if any).

## Out-of-Scope Threats

Explicitly excluded from the Phase-9 evaluation:

- **Kernel-level compromise** of the server host.
- **LLM-provider compromise** (e.g. theft of model weights,
  backdoored model serving).
- **Side channels on shared silicon** (cache-line timing,
  rowhammer, Spectre / Meltdown-class attacks). This limitation
  is honestly disclosed in the paper discussion (Phase 11) per
  Dipta et al. 2024.
- **Physical access** to the server.
- **Compromise of the upstream identity provider** (assumed
  trusted).

## Threats

The full per-boundary STRIDE enumeration is in
`docs/04_Attack_Taxonomy.md` — see the 8 STRIDE tables (one per
boundary) there. Each row in those tables carries:

- A STRIDE letter (S/T/R/I/D/E).
- A threat description.
- One or more Phase-1 ticket IDs.
- A CWE reference.

Misuse cases (concrete cross-tenant scenarios) are also in
`docs/04_Attack_Taxonomy.md` — see MC-1 through MC-4.

## Misuse Cases

Cross-references to `docs/04_Attack_Taxonomy.md`:

- **MC-1** — Cross-tenant environment-variable overwrite via
  tool shadowing (`A-NSP-001`, `A-TOL-005`, `A-MEM-002`).
- **MC-2** — Session fixation across server restart
  (`A-SES-001`, `A-SES-002`, `A-CCH-003`).
- **MC-3** — Resource path traversal via percent-encoded
  slashes (`A-RES-001`, `A-RES-002`, `A-RES-003`).
- **MC-4** — Embedding cache poisoning via prompt collision
  (`A-CCH-004`, `A-MEM-004`).

## Data-Flow Diagram

See `docs/diagrams/dfd_trust_boundaries.md` (Mermaid source)
and `docs/diagrams/dfd_trust_boundaries.svg` (rendered SVG).
The DFD shows the orchestrator ↔ MCP server ↔ Tenant A ↔ Tenant
B data flow with trust-boundary edges annotated.

## Assumptions

- Attacker has at most one legitimate tenant account.
- LLM provider is trusted; MCP server is the trust boundary
  under study.
- Network between client and server is hostile unless TLS is
  configured.
- The Phase-9 reference servers (`mcp_servers/vulnerable/` and
  `mcp_servers/secure/`, planned Phase 8) are run in
  Firecracker microVMs to limit kernel-level collateral damage
  during attack execution.