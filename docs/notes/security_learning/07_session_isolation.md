# 07 — Session Isolation

> Phase 2, Concept 7 of 14. Per `prompts/02_security_learning.md` A–F
> rubric. Concept coverage: **Isolation** macro-category.

## (A) Formal Definition

**Session isolation** is the property that the server-side state
object representing one client connection (the *session*) is
correctly bound to one principal and is not shared, reused, fixed,
or replayed across principals or connections.

Canonical security references include:

- **CWE-613 Insufficient Session Expiration** — covers sessions that
  outlive their intended lifetime.
- **CWE-384 Session Fixation** — covers the case where the attacker
  pre-mints a session the victim later uses.
- **CWE-488 Exposure of Data Element to Wrong Session** — the
  data-flow counterpart.
- **CWE-330 Use of Insufficiently Random Values** — covers
  predictable session ID generation.

## (B) Threat Model

- **Attacker position.** A tenant who can predict, fixate, or
  reuse a `session_id`; an attacker who can race a transport
  reconnection to capture state intended for another tenant.
- **Assets.** The victim's session state (caches, in-flight
  requests, cancellation tokens, SSE event queues).
- **Preconditions.** (i) Session IDs are predictable. (ii) Sessions
  are not bound to a principal. (iii) Idle / expiry policies are
  loose.

## (C) Real-World / Theoretical Example

An MCP server issues `session_id` values from a counter that resets
to zero on process restart. Tenant A connects, obtains `session_id =
0`, and populates the session with a long-running tool call. The
server restarts. Tenant B connects and is assigned `session_id = 0`
(the counter resets). Tenant B inherits Tenant A's in-flight request
state, including any partial outputs and cancellation tokens.

## (D) Standard Defenses

- **Cryptographically random session IDs.** Use `secrets.token_hex`
  (Python) / `crypto.randomBytes` (Node) with ≥128 bits of entropy.
- **Principal binding.** Sign the `session_id` with the principal's
  token; the server rejects mismatches.
- **Per-tenant session stores.** Sessions are keyed by
  `(tenant_id, session_id)`.
- **Aggressive idle / absolute expiry.** Sessions expire on the
  earlier of idle timeout or absolute lifetime.
- **Single-use session IDs.** New session on every `initialize`; the
  server never re-issues a previously-used ID.

## (E) Open Research Problems

- **Transport migration.** A session that began on `stdio` and is
  resumed on HTTP+SSE inherits trust from the original transport's
  authentication posture.
- **Distributed sessions.** Multi-replica deployments require a
  shared session store, increasing the attack surface for cross-
  replica collisions.
- **Session-bound caches.** A per-session cache that lacks a tenant
  prefix degenerates into a per-tenant cache only by accident.

## (F) Direct Relation to MCP Architecture

- **MCP boundary.** `session`, `auth`.
- **MCP primitive.** `initialize` / `notifications/initialized` /
  `shutdown` / `ping` / `notifications/cancelled`.
- **Phase-1 ticket cross-references.**
  - `A-SES-001` — fixation via predictable IDs.
  - `A-SES-002` — post-restart reuse.
  - `A-SES-003` — cross-tenant event queue.
  - `A-SES-004` — cancellation token replay.
  - `A-SES-005` — idle-window resumption.
  - `A-SES-006` — affinity header manipulation.
  - `A-SES-007` — ContextVar loss across await (cross-reference).
  - `A-SES-008` — cross-SDK context loss (cross-reference).
  - `A-SES-009` — cross-SDK cancellation semantics (cross-reference).
  - `A-AUT-007` — post-revocation session continuity
    (cross-reference).
- **Source.** `docs/notes/mcp_learning/06_sessions.md` §D–E,
  `09_sdks.md` §E.
