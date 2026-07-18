# 01 — Transport Layers

> Phase 1, Component 1 of 9. Part of the technical appendix feeding Phase 5
> (Threat Model) and Phase 7 (Attack Library). Every (E) bullet references a
> forward ticket ID of the form `A-{boundary}-{nnn}`; Phase 5 will resolve
> these IDs in `docs/04_Attack_Taxonomy.md`.

## (A) Purpose

The Model Context Protocol (MCP) defines a **transport abstraction** that
carries JSON-RPC 2.0 framed messages between an MCP client (host) and an MCP
server. The transport is the outermost trust boundary in any MCP deployment:
all higher-layer objects (tools, resources, prompts, sessions, caches) are
serialized as JSON-RPC payloads that traverse whatever transport the
deployment selects. Three transports are documented in the public
specification: `stdio` (process pipes), HTTP + Server-Sent Events (SSE), and
streamable HTTP. The transport determines framing, multiplexing, lifecycle,
and reconnection semantics — and consequently determines the set of
realistic on-path adversaries.

## (B) Internal Workflow

MCP is JSON-RPC 2.0 framed (RFC 7455). Two message directions coexist on
every transport:

- **Requests** — `{"jsonrpc":"2.0","id":<n>,"method":"...","params":{...}}`.
- **Notifications** — same envelope minus `id`.
- **Responses** — `{"jsonrpc":"2.0","id":<n>,"result":{...}}` or
  `{"jsonrpc":"2.0","id":<n>,"error":{"code":-32601,"message":"..."}}`.

Lifecycle (transport-specific):

| Transport | Connection lifecycle | Ordering guarantee | Reconnect model |
|---|---|---|---|
| `stdio` | Process spawned by host; one server per stdin/stdout pair | Inherently FIFO per pipe | Respawn required; no spec-defined resumption token (spec section requires empirical verification) |
| HTTP + SSE | Client opens HTTP POST; server replies via SSE stream; one stream per request or per session | Stream order = request order on same connection | Spec section requires empirical verification; resumability depends on server |
| Streamable HTTP | Bidirectional HTTP streaming (spec section requires empirical verification) | Stream-scoped | Resumability per session |

Ordering constraints common to all transports:

1. `initialize` request → `initialize` response → `notifications/initialized`.
2. After step 1, requests and notifications may be interleaved subject to
   the per-transport FIFO guarantee.
3. `shutdown` is best-effort; the spec does not mandate a graceful close
   handshake (spec section requires empirical verification).

## (C) Data Flow

A `stdio` request framed in MCP:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_docs",
    "arguments": {"q": "MCP isolation"}
  }
}
```

A response (success and error variants):

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {"content": [{"type": "text", "text": "..."}]}
}
```

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {"code": -32601, "message": "Method not found"}
}
```

A streaming event over SSE (HTTP+SSE transport):

```
event: message
data: {"jsonrpc":"2.0","method":"notifications/progress","params":{"progressToken":"...","value":0.5}}

```

Inputs / outputs per transport:

| Transport | Input framing | Output framing | Multiplexing |
|---|---|---|---|
| `stdio` | Newline-delimited JSON over stdin | Newline-delimited JSON over stdout; logs on stderr | One logical client per pipe |
| HTTP + SSE | `Content-Type: application/json` POST body | `text/event-stream` SSE frames | Multiple concurrent HTTP connections; per-connection scope |
| Streamable HTTP | HTTP chunked transfer (spec section requires empirical verification) | Same channel | Session-scoped (spec section requires empirical verification) |

## (D) Inherent Security Implications

- **Process boundary as TCB.** On `stdio`, the OS process is the trust
  boundary. Subprocesses inherit the host's UID, env, file descriptors, and
  signal handlers. A misconfigured MCP server therefore has the same blast
  radius as the host process.
- **No built-in tenant identity at the transport layer.** The transport
  carries `jsonrpc` envelopes but no required `tenant_id` field. Any tenant
  multiplexing must be implemented above the transport (typically by the
  server's session logic).
- **SSE origin policy.** Browsers implementing an MCP client over SSE are
  subject to standard CORS / cookie-without-SameSite risks (RFC 7455 §6
  not directly applicable; HTTP semantics from RFC 9110 apply).
- **No spec-mandated mTLS.** The reference servers ship with HTTP+SSE
  examples that are unauthenticated by default (spec section requires
  empirical verification for current revision).
- **Framing ambiguity.** `stdio` reads/writes newline-delimited JSON. A
  malicious host can interleave framing bytes (newlines inside large
  arguments) if the server does not bound message length or use length
  prefixes (spec section requires empirical verification).
- **Reconnect replay.** Without a documented resumption token, a reconnect
  may replay notifications or accept duplicate `initialize` calls; the
  observable behavior is server-specific (spec section requires empirical
  verification).
- **Logging.** Default logging often writes the full JSON-RPC payload,
  including tool arguments. This is a confidentiality footgun: arguments
  frequently contain tenant PII.

## (E) Theoretical Attack Surface

- **E-1.** A malicious host on `stdio` can **inject CRLF / framing bytes**
  inside string arguments to splice a forged JSON-RPC envelope. →
  `A-TRN-001` (transport: framing smuggling).
- **E-2.** A passive on-path adversary on HTTP+SSE can **observe tool
  arguments and results** unless the deployment adds TLS. →
  `A-TRN-002` (transport: cleartext disclosure).
- **E-3.** An active MITM can **replay or reorder** SSE events after a
  legitimate `initialize`, exploiting missing resumption tokens. →
  `A-TRN-003` (transport: replay / reorder).
- **E-4.** A server that emits tool arguments into **stderr / logs**
  creates a side channel readable by any process with file-descriptor
  access (e.g. journalctl, container log scrapers). →
  `A-TRN-004` (transport: log-channel leakage).
- **E-5.** An attacker who can spawn a second `stdio` child can
  **impersonate** any tenant to a server that multiplexes many tenants
  through one process, because no per-pipe tenant identity is provided by
  the transport. → `A-TRN-005` (transport: cross-tenant impersonation via
  shared stdio worker).
- **E-6.** A hostile SSE client can issue **server-sent event injection**:
  forge `event:` / `data:` frames to mislead the client UI about
  notification origin. → `A-TRN-006` (transport: SSE frame injection).
- **E-7.** Process-level side channels (file-descriptor inheritance,
  inherited environment, shared `/proc` namespaces) leak the host's
  secrets into the MCP server. → `A-TRN-007` (transport: process
  inheritance leakage).

All ticket IDs reference forward entries in
`docs/04_Attack_Taxonomy.md` and will be materialised by Phase 5.
