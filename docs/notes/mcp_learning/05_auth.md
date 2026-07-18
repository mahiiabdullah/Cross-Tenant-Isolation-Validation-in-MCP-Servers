# 05 — Authentication & Authorization Boundaries

> Phase 1, Component 5 of 9. Every (E) bullet references a forward ticket ID
> of the form `A-{boundary}-{nnn}`; Phase 5 will resolve these IDs in
> `docs/04_Attack_Taxonomy.md`.

## (A) Purpose

Authentication in MCP is the binding between a **transport-level identity**
(a bearer token, mTLS cert, or process identity) and a **logical principal**
(the tenant that the server will subsequently attribute requests to).
Authorization is the per-method policy that decides whether a given
principal may invoke a given tool, read a given resource, or fetch a given
prompt. Auth is the **root trust boundary**: every higher-boundary
guarantee collapses if the principal mapping is wrong.

## (B) Internal Workflow

The spec defines `initialize` as the first message on a transport; it
includes a `protocolVersion` and a `capabilities` object:

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "initialize",
  "params": {
    "protocolVersion": "<version>",
    "capabilities": {},
    "clientInfo": {"name": "example-client", "version": "0.1.0"}
  }
}
```

The client then sends `notifications/initialized`. Both directions may
include authentication material; the exact channel depends on the
transport:

| Transport | Auth channel |
|---|---|
| `stdio` | Process identity, env vars, or a token passed via process arg (spec section requires empirical verification for canonical pattern) |
| HTTP + SSE | `Authorization: Bearer <token>` header; cookies; mTLS at the HTTP layer |
| Streamable HTTP | Same as HTTP + SSE (spec section requires empirical verification) |

Authorization decisions are made per request: the server inspects the
method and params, resolves the principal from the auth material, looks
up the principal's allowed-tools / allowed-resources, and either dispatches
or returns `-32001` (or another implementation-defined error code; spec
section requires empirical verification for the canonical mapping).

The spec does **not** mandate a specific token format or scope grammar;
common choices in reference servers include opaque bearer tokens with a
shared secret lookup, OAuth 2.0 bearer tokens, and mTLS client certs.

## (C) Data Flow

Token issuance (deployment-time, out-of-band):

```
[identity provider]
        │
        ▼  (issues token bound to: tenant_id, scopes, audience, exp)
[token]
        │
        ▼  (sent on every transport request)
[MCP server auth middleware]
        │
        ▼  (resolves tenant_id, attaches to session)
[handler dispatch]
```

Token verification on each request:

```json
{
  "headers": {
    "Authorization": "Bearer eyJhbGciOi..."
  },
  "body": {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {"name": "search_docs", "arguments": {}}
  }
}
```

The server extracts the token, validates signature + expiry + audience,
maps to a principal, and proceeds. Tokens typically carry a
`tenant_id` claim; the protocol does not require a specific claim name
(spec section requires empirical verification for canonical claim names
in current SDK defaults).

## (D) Inherent Security Implications

- **No spec-mandated audience.** Tokens are accepted if the server can
  verify their signature, regardless of intended audience. Cross-deployment
  token reuse is possible.
- **No scope grammar.** Reference servers typically accept any valid
  token and resolve principal at the server-side mapping table. There is
  no protocol-level concept of "scope X is required to call method Y."
- **Token forwarding risk.** A tool whose handler accepts user-supplied
  URLs and fetches them can be coerced into forwarding the Authorization
  header to an attacker-controlled origin (SSRF + token leak).
- **Process identity on stdio.** On `stdio`, the only auth signal may be
  the OS UID of the host process. Two hosts sharing the same UID look
  identical to the server.
- **mTLS not required.** Reference deployments over HTTP+SSE frequently
  run without TLS at all; the spec does not mandate transport encryption.
- **Session token as bearer.** Once a session is established, subsequent
  requests are authenticated by the session ID. If the session ID leaks
  (logs, error messages, cache keys) the attacker inherits the principal.
- **Capability negotiation trust.** The `capabilities` field in
  `initialize` is self-asserted; a malicious client can advertise
  capabilities it does not possess without consequence.
- **Authorization on tool name alone.** If the policy is "deny tool X
  for tenant Y," an attacker who renames the call to a synonym or a
  shadow tool may bypass.

## (E) Theoretical Attack Surface

- **E-1.** A malicious host captures an Authorization header from logs
  or error traces and **replays** it against the server. →
  `A-AUT-002` (auth: token replay across transports).
- **E-2.** A token issued for deployment A is **misused against
  deployment B** because no `aud` claim is enforced. →
  `A-AUT-003` (auth: cross-deployment token reuse).
- **E-3.** A tenant calls a tool whose handler **SSRF-fetches** a URL
  and forwards the original Authorization header. →
  `A-AUT-004` (auth: token forwarding via SSRF).
- **E-4.** A malicious client **advertises capabilities** it does not
  possess to elicit different server behavior (e.g. server skips a
  compatibility check). → `A-AUT-005` (auth: capability negotiation
  spoofing).
- **E-5.** A session token is **logged in a cache key** (e.g. cache key
  includes session ID for debugging), exposing it to anyone with read
  access to the cache. → `A-CCH-002` (cache: session-token leakage
  via cache key; cross-referenced).
- **E-6.** A tenant's mTLS client cert has its **SAN / CN** spoofed
  because the server does not pin the CA chain. →
  `A-AUT-006` (auth: mTLS SAN spoofing).
- **E-7.** A server authorizes on `tool_name` but a malicious tenant
  invokes a **shadow tool** whose name the policy does not list.
  → `A-NSP-005` (namespace: authorization bypass via shadow tool;
  cross-referenced).

All ticket IDs reference forward entries in
`docs/04_Attack_Taxonomy.md` and will be materialised by Phase 5.