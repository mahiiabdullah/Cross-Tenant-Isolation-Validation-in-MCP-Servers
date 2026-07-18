# 06 — Session Lifecycle & State Management

> Phase 1, Component 6 of 9. Every (E) bullet references a forward ticket ID
> of the form `A-{boundary}-{nnn}`; Phase 5 will resolve these IDs in
> `docs/04_Attack_Taxonomy.md`.

## (A) Purpose

An MCP **session** is the server-side state object that ties together a
sequence of JSON-RPC requests from one client. Sessions typically hold
the resolved principal, per-session caches, in-flight cancellation
tokens, and any per-connection buffers (SSE event queues, buffered
notifications). Session lifecycle is the second-most consequential trust
boundary after auth: a session that is shared, reused, or fixed across
tenants is a tenant-mixing primitive.

## (B) Internal Workflow

A session begins when the server accepts a transport connection and
completes `initialize` / `notifications/initialized`. It ends when the
client issues a `shutdown` request, the transport closes, or a
server-defined idle/expiry timer fires (spec section requires empirical
verification for canonical timeout defaults).

Primary lifecycle messages:

- `initialize` (request) — start a session.
- `notifications/initialized` (notification) — client confirms it is ready.
- `ping` (request) — keep-alive; many servers treat it as a no-op
  acknowledgement.
- `shutdown` (request) — request a graceful close (spec section requires
  empirical verification for whether it is mandatory).
- `notifications/cancelled` (notification) — cancel an in-flight request
  identified by a previously-issued progress token.

Server-side session storage typically uses one of:

| Pattern | Shape | Tenant-isolation property |
|---|---|---|
| In-process dict | `dict[session_id, SessionState]` | Strong only if session_id is unguessable and never reused |
| External store (Redis, DB) | keyed lookup | Strong only if key includes tenant_id |
| Token-bound state | signed JWT contains session state | Strong only if the JWT's tenant claim is verified |

## (C) Data Flow

Session establishment (HTTP+SSE example):

```
client                            server
  |  ---- POST /messages (initialize) --->  |
  |                                         |  verify token, mint session_id,
  |                                         |  bind session_id -> principal
  |  <----------- SSE stream --------------  |
  |                                         |
  |  ---- POST /messages (initialized) ----> |
  |                                         |
  |  ---- POST /messages (tools/call) ---->  |
  |  <--------- SSE event (result) --------  |
```

Session state is referenced by `session_id` on subsequent requests:

```json
{
  "headers": {"Mcp-Session-Id": "sess-7f3a"},
  "body": {
    "jsonrpc": "2.0",
    "id": 33,
    "method": "tools/call",
    "params": {"name": "search_docs", "arguments": {}}
  }
}
```

The exact header / parameter name varies by transport and SDK; the spec
section requires empirical verification for the canonical field.

Cancellation:

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/cancelled",
  "params": {"requestId": 33, "reason": "user requested"}
}
```

## (D) Inherent Security Implications

- **Session fixation.** If the server accepts a client-supplied
  `session_id` (or derives it from a predictable source like a hash of
  the source IP), an attacker can pre-mint a session they later
  share with a victim.
- **Session reuse across tenants.** A server that pools sessions in
  memory by `session_id` only, without `tenant_id` in the lookup key,
  will hand Tenant A's state to Tenant B if both end up with the same
  `session_id` (e.g. after a restart that resets the counter).
- **Cross-transport session reuse.** If the same session is valid on
  stdio and HTTP+SSE, a stolen `session_id` from a less-protected
  transport escalates to the more-protected one.
- **Idle / expiry policy.** A long-lived session that is never
  invalidated allows a captured `session_id` indefinite use.
- **Cancellation race.** `notifications/cancelled` for an in-flight
  request may arrive after the response is partially written; the
  server must ensure partial state is not exposed to a different
  session.
- **Session-bound caches.** If per-session caches are keyed on
  `session_id` only, two sessions owned by the same tenant but on
  different transports may diverge; if the cache key omits `tenant_id`,
  two tenants can collide.

## (E) Theoretical Attack Surface

- **E-1.** A malicious client **fixates** a `session_id` it knows (e.g.
  generated from a low-entropy source) and lures a victim to use the
  same transport, then resumes the victim's session. →
  `A-SES-001` (session: fixation via predictable IDs).
- **E-2.** A server reuses a `session_id` after restart, causing
  Tenant B to inherit Tenant A's state from a prior run. →
  `A-SES-002` (session: post-restart reuse).
- **E-3.** A session-bound **SSE event queue** is shared across
  tenants because the queue is keyed on `session_id` only and two
  tenants obtained the same `session_id` via a load-balancer bug.
  → `A-SES-003` (session: cross-tenant event queue).
- **E-4.** A cancellation token from Tenant A is replayed by Tenant
  B to abort Tenant B's request — but the server matches the token
  to the wrong in-flight request. → `A-SES-004` (session: cancellation
  token replay).
- **E-5.** A long-lived session continues to authorize tool calls
  after the principal's token has been **revoked**, because the
  server does not re-check expiry on each request. →
  `A-AUT-007` (auth: post-revocation session continuity;
  cross-referenced).
- **E-6.** A tenant logs out (closes transport) but the server's
  **idle sweeper** is delayed, allowing a co-located attacker to
  resume the session within the grace window. →
  `A-SES-005` (session: idle-window resumption).
- **E-7.** A server uses **sticky session IDs** derived from
  upstream proxy headers, allowing an attacker who controls a header
  to pre-assign session affinity. → `A-SES-006` (session: affinity
  header manipulation).

All ticket IDs reference forward entries in
`docs/04_Attack_Taxonomy.md` and will be materialised by Phase 5.