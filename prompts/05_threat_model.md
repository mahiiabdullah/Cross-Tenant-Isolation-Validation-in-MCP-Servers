# 05 — Threat Model Prompt

> **Phase 5.** Formalize the security boundaries using standard academic
> frameworks. Iterates on `docs/02_Threat_Model.md`.

## Method

Use a **hybrid STRIDE + trust-boundary** approach.

## Required Outputs

### 1. System Definition

- **Assets.** Data, credentials, sessions, embeddings, tool outputs.
- **Actors.** Honest Tenant, Malicious Tenant, Compromised Agent, Malicious
  MCP Server, Network Adversary, Server Admin.
- **Trust Boundaries.** Inter-component boundaries where the threat model
  changes (transport, session, namespace, tool, resource, memory, cache, auth).

### 2. Attacker Capabilities (in scope)

- Has execution rights in Tenant A.
- Can register tools / read resources / call any public method on the server.
- Can inject content via prompt, resource, or tool result.
- **Cannot** access host OS, cannot mint signed server tokens out-of-band.

### 3. Out-of-Scope Threats

Explicitly exclude: kernel-level compromise, LLM provider compromise, side
channels on shared silicon.

### 4. STRIDE per Boundary

Apply STRIDE to each: tool namespace, context window, session tokens,
resources, memory store, cache, auth, transport.

### 5. Misuse Cases (≥3 concrete scenarios)

Example: *Tenant A uses tool injection to overwrite Tenant B's environment
variables by hijacking a common tool name.*

### 6. Data Flow Diagram

Generate a Mermaid.js code block for a DFD showing trust boundaries between
the orchestrator, the MCP server, Tenant A, and Tenant B. Save rendered SVG to
`docs/diagrams/dfd_trust_boundaries.svg`.

## Repo Deliverables

- `docs/02_Threat_Model.md` finalized.
- `docs/diagrams/dfd_trust_boundaries.svg` rendered.
- An attack ticket per (boundary × STRIDE) row in `attacks/<boundary>/<id>.py`
  (initially a stub).

## Done When

- [ ] All 8 boundaries have STRIDE rows.
- [ ] ≥3 misuse cases each have a concrete attack ticket ID.
- [ ] Every attack in `attacks/` references a STRIDE row in this document.
