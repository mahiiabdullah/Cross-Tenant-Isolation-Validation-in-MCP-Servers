# 00 — MCP Technical Appendix (Consolidated)

> Consolidated appendix for **Phase 1** of the MCP Isolation Research
> program. This file aggregates the nine component files in
> `docs/notes/mcp_learning/` into a single paper-ready appendix.
> Source files are individually maintained and authoritative; this file is
> regenerated from them.
>
> This appendix must render with no `TBD` markers and must
> reference all forward ticket IDs of the form
> `A-{boundary}-{nnn}` to be materialised in
> `docs/04_Attack_Taxonomy.md`.

---

## Table of Contents

1. Transport Layers — see `01_transport.md`
2. Tools & Tool Execution Routing — see `02_tools_routing.md`
3. Resources & Resource Templates — see `03_resources.md`
4. Prompts & Context Injection Mechanisms — see `04_prompts_context.md`
5. Authentication & Authorization Boundaries — see `05_auth.md`
6. Session Lifecycle & State Management — see `06_sessions.md`
7. Context Management & Memory Persistence — see `07_context_memory.md`
8. Multi-Client to Single-Server Concurrency — see `08_concurrency.md`
9. Official SDK Implementation Nuances — see `09_sdks.md`

---

## 1. Transport Layers

### (A) Purpose

The Model Context Protocol (MCP) defines a **transport abstraction** that
carries JSON-RPC 2.0 framed messages between an MCP client (host) and an
MCP server. The transport is the outermost trust boundary in any MCP
deployment: all higher-layer objects (tools, resources, prompts, sessions,
caches) are serialized as JSON-RPC payloads that traverse whatever
transport the deployment selects. Three transports are documented in the
public specification: `stdio` (process pipes), HTTP + Server-Sent Events
(SSE), and streamable HTTP. The transport determines framing,
multiplexing, lifecycle, and reconnection semantics — and consequently
determines the set of realistic on-path adversaries.

### (B) Internal Workflow

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

### (C) Data Flow

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

### (D) Inherent Security Implications

- **Process boundary as TCB.** On `stdio`, the OS process is the trust
  boundary. Subprocesses inherit the host's UID, env, file descriptors,
  and signal handlers.
- **No built-in tenant identity at the transport layer.** The transport
  carries `jsonrpc` envelopes but no required `tenant_id` field.
- **SSE origin policy.** Browsers implementing an MCP client over SSE
  are subject to standard CORS / cookie-without-SameSite risks (RFC
  7455 §6 not directly applicable; HTTP semantics from RFC 9110
  apply).
- **No spec-mandated mTLS.** The reference servers ship with HTTP+SSE
  examples that are unauthenticated by default (spec section requires
  empirical verification for current revision).
- **Framing ambiguity.** `stdio` reads/writes newline-delimited JSON.
  A malicious host can interleave framing bytes (newlines inside large
  arguments) if the server does not bound message length or use length
  prefixes (spec section requires empirical verification).
- **Reconnect replay.** Without a documented resumption token, a
  reconnect may replay notifications or accept duplicate `initialize`
  calls; the observable behavior is server-specific (spec section
  requires empirical verification).
- **Logging.** Default logging often writes the full JSON-RPC payload,
  including tool arguments. This is a confidentiality footgun.

### (E) Theoretical Attack Surface

- **E-1.** A malicious host on `stdio` can **inject CRLF / framing
  bytes** inside string arguments to splice a forged JSON-RPC envelope.
  → `A-TRN-001` (transport: framing smuggling).
- **E-2.** A passive on-path adversary on HTTP+SSE can **observe tool
  arguments and results** unless the deployment adds TLS. →
  `A-TRN-002` (transport: cleartext disclosure).
- **E-3.** An active MITM can **replay or reorder** SSE events after
  a legitimate `initialize`, exploiting missing resumption tokens. →
  `A-TRN-003` (transport: replay / reorder).
- **E-4.** A server that emits tool arguments into **stderr / logs**
  creates a side channel readable by any process with file-descriptor
  access. → `A-TRN-004` (transport: log-channel leakage).
- **E-5.** An attacker who can spawn a second `stdio` child can
  **impersonate** any tenant to a server that multiplexes many tenants
  through one process, because no per-pipe tenant identity is provided
  by the transport. → `A-TRN-005` (transport: cross-tenant
  impersonation via shared stdio worker).
- **E-6.** A hostile SSE client can issue **server-sent event
  injection**: forge `event:` / `data:` frames to mislead the client
  UI about notification origin. → `A-TRN-006` (transport: SSE frame
  injection).
- **E-7.** Process-level side channels (file-descriptor inheritance,
  inherited environment, shared `/proc` namespaces) leak the host's
  secrets into the MCP server. → `A-TRN-007` (transport: process
  inheritance leakage).

---

## 2. Tools & Tool Execution Routing

### (A) Purpose

The **Tool** primitive is the central capability exposed by an MCP
server. A tool is a named, parameterised function with a JSON-Schema-style
input contract and a structured output. Tool **routing** is the path
from a client issuing `tools/call` to the server-side handler that
executes the action and returns a `content` block. Routing correctness
is the prerequisite for isolating tenants from each other's capabilities:
a routing bug that dispatches a call to the wrong handler is an
immediate isolation failure.

### (B) Internal Workflow

Three primary methods:

- `tools/list` — enumerate tool descriptors.
- `tools/call` — invoke a named tool with arguments.
- `notifications/tools/list_changed` — server-pushed notification that
  the tool catalog changed (spec section requires empirical
  verification for whether clients are required to re-list).

Tool descriptor shape (spec section requires empirical verification for
the canonical field set; the following reflects the publicly documented
baseline):

```json
{
  "name": "search_docs",
  "description": "Search internal documentation.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "q": {"type": "string"},
      "limit": {"type": "integer", "default": 10}
    },
    "required": ["q"]
  }
}
```

`tools/call` request:

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "tools/call",
  "params": {
    "name": "search_docs",
    "arguments": {"q": "MCP isolation", "limit": 5}
  }
}
```

### (C) Data Flow

| Stage | Input | Decision basis | Output |
|---|---|---|---|
| Authenticate | JSON-RPC request | Token / scope check | Authorised call or `-32001`-class error |
| Resolve tool | `params.name` | Internal name table | Handler reference or `-32601` Method not found |
| Validate args | `params.arguments` | `inputSchema` (jsonschema) | Validated args or `-32602` Invalid params |
| Dispatch | Handler invocation | Tenant context bound at session | Result `content` array |
| Sanitise result | Raw handler output | Server-defined policy | `content` array (may be redacted) |

### (D) Inherent Security Implications

- **Implicit trust in tool output.** Tool outputs are typically rendered
  back into the model's context window. The protocol does not specify a
  trust marker on returned `content`; the client decides what to do.
- **Schema confusion.** If a tool's `inputSchema` accepts arbitrary
  additional properties, an attacker can smuggle fields the handler
  ignores client-side but interprets server-side (or vice versa).
- **Tool-name squatting.** A server may register a tool whose name
  collides with a built-in or another tenant's preferred tool name.
- **No result sanitisation requirement.** The protocol does not require
  stripping control characters, ANSI escapes, or hidden instructions
  from `content` before returning them to the client.
- **Side-effecting tools.** Some tools (write to disk, send email, run
  a shell command) have effects outside the protocol.
- **Dynamic registration.** Servers may register tools at runtime via
  in-band mechanisms; a compromised agent that triggers registration
  may introduce a tool the host did not intend to expose.

### (E) Theoretical Attack Surface

- **E-1.** A malicious server returns a `content` array whose `text`
  includes **hidden instructions** the model treats as commands
  (indirect prompt injection via tool result). → `A-TOL-001` (tool:
  result-borne prompt injection).
- **E-2.** A tenant crafts a `tools/call` whose `arguments` contain
  **schema-confusing extra fields** that a careless handler
  deserialises. → `A-TOL-002` (tool: schema-confusion argument
  smuggling).
- **E-3.** A server registers a tool under a name that **shadows** a
  built-in (`read_file`, `exec`, `shell`). A confused-deputy call
  reaches the wrong handler. → `A-NSP-001` (namespace: tool
  shadowing).
- **E-4.** A tenant invokes a tool that **leaks another tenant's
  arguments** from a shared in-memory queue. → `A-TOL-003` (tool:
  cross-tenant context capture).
- **E-5.** A malicious tool handler emits a `content` array with a
  `type` value not in the documented set, exploiting lenient client
  parsers. → `A-TOL-004` (tool: type-confusion result).
- **E-6.** A tool whose description advertises benign behaviour
  actually **dispatches to a side-effecting handler** based on hidden
  `arguments` keys. → `A-TOL-005` (tool: handler-mismatch
  invocation).
- **E-7.** Tool results are cached by `(tool_name, arguments)` key,
  allowing **cross-tenant cache poisoning** when the key omits
  `tenant_id`. → `A-CCH-001` (cache: cross-tenant cache poisoning
  via tool key).

---

## 3. Resources & Resource Templates

### (A) Purpose

A **Resource** in MCP is a server-managed, addressable artifact —
typically a file, blob, or URI-identified record — that a client can
read, subscribe to, or enumerate. Resource **templates** are URI
patterns with parameters, allowing a client to materialise a concrete
resource URI at runtime. The resource layer is the file-system /
object-store analogue of the tool layer and is the second most
consequential capability surface for cross-tenant leakage.

### (B) Internal Workflow

Primary methods:

- `resources/list` — enumerate concrete resources visible to the
  calling client.
- `resources/templates/list` — enumerate URI templates.
- `resources/read` — fetch the bytes of a specific resource URI.
- `resources/subscribe` — register interest in change notifications
  for a URI (spec section requires empirical verification).
- `notifications/resources/updated` — server-pushed notification that a
  subscribed resource changed.
- `notifications/resources/list_changed` — server-pushed notification
  that the resource catalog changed.

### (C) Data Flow

`resources/read` request:

```json
{
  "jsonrpc": "2.0",
  "id": 11,
  "method": "resources/read",
  "params": {"uri": "file:///tenant-a/docs/x.md"}
}
```

`resources/read` response (text blob):

```json
{
  "jsonrpc": "2.0",
  "id": 11,
  "result": {
    "contents": [
      {
        "uri": "file:///tenant-a/docs/x.md",
        "mimeType": "text/markdown",
        "text": "# Heading\n..."
      }
    ]
  }
}
```

### (D) Inherent Security Implications

- **URI is the only access-control handle.** The server receives a URI
  string and must enforce tenant scoping on it; there is no
  protocol-level per-resource ACL.
- **Path traversal.** A naive resolver that concatenates tenant root
  with a URI path (`..%2F..%2Ftenant-b/...`) escapes the tenant's
  scope.
- **Symlink following.** If the server follows symlinks, a tenant can
  point at another tenant's data.
- **No tenant scoping in URI scheme.** URI syntax does not embed a
  required `tenant_id`; the server must enforce scoping itself.
- **Subscription fan-out.** `resources/subscribe` notifies on changes;
  if subscription state is shared across tenants, notifications can
  leak resource existence to the wrong tenant.
- **Pagination / listing leakage.** `resources/list` may return more
  than the requesting tenant should see if the server filters only on
  the requester's identity but caches across sessions.
- **Template parameter trust.** A malicious client can request a
  template URI with values designed to escape the pattern.

### (E) Theoretical Attack Surface

- **E-1.** A malicious client supplies a URI like
  `file:///tenant-a/../tenant-b/secrets.txt` and the resolver
  **path-traverses** to another tenant. → `A-RES-001` (resource:
  path traversal across tenants).
- **E-2.** A malicious client supplies a URI containing
  **percent-encoded slashes** or **double-encoded** characters to
  bypass a naive string-prefix check. → `A-RES-002` (resource: URI
  normalisation bypass).
- **E-3.** A tenant plants a **symlink** inside its own resource tree
  that points to another tenant's resource; the resolver follows the
  symlink. → `A-RES-003` (resource: symlink escape).
- **E-4.** A `resources/subscribe` call from Tenant A causes
  `notifications/resources/updated` events for **Tenant B's**
  resource to be delivered to A because the subscription registry is
  keyed on URI alone. → `A-RES-004` (resource: subscription
  cross-tenant leak).
- **E-5.** A `resources/list` response **includes resources from
  other tenants** because the server's list query omits a tenant
  predicate. → `A-RES-005` (resource: enumeration leakage).
- **E-6.** A tenant registers a URI template whose pattern overlaps
  an existing built-in (`file:///{tenant}/...`) and **intercepts**
  reads for adjacent tenants. → `A-NSP-002` (namespace:
  resource-template shadowing).
- **E-7.** A `resources/read` response embeds **content** (text or
  blob) that contains instructions the model treats as commands. →
  `A-RES-006` (resource: indirect prompt injection via content).

---

## 4. Prompts & Context Injection Mechanisms

### (A) Purpose

The MCP **Prompts** primitive is a server-managed template that the
client (client application) renders into a string and inserts into the
model's context window. Prompts are *how* servers inject structured
guidance (system messages, tool-use instructions, contextual data) into
the model. Because the resulting string becomes part of the model's
input, prompts are the most direct route for **in-band context
injection** — both legitimate and malicious.

### (B) Internal Workflow

Primary methods:

- `prompts/list` — enumerate prompt templates.
- `prompts/get` — fetch a rendered prompt given a name and arguments.
- `notifications/prompts/list_changed` — server-pushed change
  notification (spec section requires empirical verification).

### (C) Data Flow

Template variables flow through three trust boundaries before they
reach the model:

```
[user input / tool result / resource content]
        │
        ▼  (server may concatenate / interpolate)
[arguments object in prompts/get]
        │
        ▼  (server renders template)
[messages[].content.text]
        │
        ▼  (client host inserts into model context)
[model's input sequence]
```

Each arrow is an attacker-controlled join point when any of the
upstream inputs originate from a tenant other than the requesting one.

### (D) Inherent Security Implications

- **No content trust marker.** The `messages[].content` envelope has
  no field that says "this text came from a tenant other than the
  requester." The model has no way to distinguish prompt-template text
  from user text from tool-result text.
- **Indirect injection is in-band.** When a prompt template
  interpolates a resource URI or a tool result, the resulting text
  becomes a covert channel between tenants.
- **Prompt name squatting.** A server may register a prompt whose name
  collides with a built-in or with a prompt another tenant's
  automation fetches automatically.
- **Argument smuggling.** A prompt template may concatenate arguments
  into the rendered text without quoting, enabling injection of
  arbitrary model-facing content via crafted argument values.
- **Auto-injection by host.** Hosts that auto-call `prompts/get` on
  startup create a code-execution-like channel.
- **No origin audit.** The protocol does not require the rendered
  prompt to record which template and which arguments produced it.

### (E) Theoretical Attack Surface

- **E-1.** A malicious server (or a tenant who controls a tool result)
  embeds instructions inside a tool output that is later rendered into
  a prompt template, achieving **indirect prompt injection** across
  tenants. → `A-TOL-006` (tool: indirect injection via prompt
  re-rendering).
- **E-2.** A prompt template uses **unsafe string interpolation** on
  an argument value, letting the caller break out of the intended
  context block and inject a new role. → `A-NSP-003` (namespace:
  prompt-template argument injection).
- **E-3.** A tenant registers a prompt name that **shadows** a
  built-in (`/help`, `/system`) so the host auto-renders the
  attacker-controlled text. → `A-NSP-004` (namespace: prompt name
  squatting).
- **E-4.** A prompt template contains **cached embeddings** of prior
  tenants' conversations that get re-injected into the current model's
  context because the cache key omits tenant identity. →
  `A-MEM-001` (memory: cross-tenant prompt cache re-injection).
- **E-5.** A prompt template interpolates **resource content** whose
  blob includes hidden instructions, achieving injection via the
  resource layer. → `A-RES-007` (resource: indirect prompt injection
  via prompt interpolation).
- **E-6.** A host that auto-injects prompts on `initialize` runs the
  server's prompt at **startup**; a malicious server uses this channel
  to seed the model with attacker-chosen system-level instructions.
  → `A-AUT-001` (auth: startup-time prompt injection via session
  establishment).
- **E-7.** A prompt template's `description` field contains
  instructions the host mistakenly renders into the model's context.
  → `A-TOL-007` (tool/prompt: description-channel injection).

---

## 5. Authentication & Authorization Boundaries

### (A) Purpose

Authentication in MCP is the binding between a **transport-level
identity** (a bearer token, mTLS cert, or process identity) and a
**logical principal** (the tenant that the server will subsequently
attribute requests to). Authorization is the per-method policy that
decides whether a given principal may invoke a given tool, read a
given resource, or fetch a given prompt. Auth is the **root trust
boundary**: every higher-boundary guarantee collapses if the principal
mapping is wrong.

### (B) Internal Workflow

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

| Transport | Auth channel |
|---|---|
| `stdio` | Process identity, env vars, or a token passed via process arg (spec section requires empirical verification for canonical pattern) |
| HTTP + SSE | `Authorization: Bearer <token>` header; cookies; mTLS at the HTTP layer |
| Streamable HTTP | Same as HTTP + SSE (spec section requires empirical verification) |

### (C) Data Flow

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

### (D) Inherent Security Implications

- **No spec-mandated audience.** Tokens are accepted if the server can
  verify their signature, regardless of intended audience.
- **No scope grammar.** Reference servers typically accept any valid
  token and resolve principal at the server-side mapping table.
- **Token forwarding risk.** A tool whose handler accepts user-supplied
  URLs and fetches them can be coerced into forwarding the
  Authorization header to an attacker-controlled origin (SSRF + token
  leak).
- **Process identity on stdio.** On `stdio`, the only auth signal may
  be the OS UID of the host process.
- **mTLS not required.** Reference deployments over HTTP+SSE frequently
  run without TLS at all.
- **Session token as bearer.** Once a session is established,
  subsequent requests are authenticated by the session ID.
- **Capability negotiation trust.** The `capabilities` field in
  `initialize` is self-asserted.
- **Authorization on tool name alone.** If the policy is "deny tool X
  for tenant Y," an attacker who renames the call to a synonym may
  bypass.

### (E) Theoretical Attack Surface

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
  possess to elicit different server behavior. → `A-AUT-005` (auth:
  capability negotiation spoofing).
- **E-5.** A session token is **logged in a cache key** (e.g. cache
  key includes session ID for debugging), exposing it to anyone with
  read access to the cache. → `A-CCH-002` (cache: session-token
  leakage via cache key).
- **E-6.** A tenant's mTLS client cert has its **SAN / CN** spoofed
  because the server does not pin the CA chain. →
  `A-AUT-006` (auth: mTLS SAN spoofing).
- **E-7.** A server authorizes on `tool_name` but a malicious tenant
  invokes a **shadow tool** whose name the policy does not list. →
  `A-NSP-005` (namespace: authorization bypass via shadow tool).

---

## 6. Session Lifecycle & State Management

### (A) Purpose

An MCP **session** is the server-side state object that ties together a
sequence of JSON-RPC requests from one client. Sessions typically hold
the resolved principal, per-session caches, in-flight cancellation
tokens, and any per-connection buffers (SSE event queues, buffered
notifications). Session lifecycle is the second-most consequential
trust boundary after auth: a session that is shared, reused, or fixed
across tenants is a tenant-mixing primitive.

### (B) Internal Workflow

A session begins when the server accepts a transport connection and
completes `initialize` / `notifications/initialized`. It ends when the
client issues a `shutdown` request, the transport closes, or a
server-defined idle/expiry timer fires (spec section requires empirical
verification for canonical timeout defaults).

Primary lifecycle messages:

- `initialize` (request) — start a session.
- `notifications/initialized` (notification) — client confirms it is
  ready.
- `ping` (request) — keep-alive.
- `shutdown` (request) — request a graceful close (spec section
  requires empirical verification for whether it is mandatory).
- `notifications/cancelled` (notification) — cancel an in-flight
  request identified by a previously-issued progress token.

### (C) Data Flow

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

### (D) Inherent Security Implications

- **Session fixation.** If the server accepts a client-supplied
  `session_id` (or derives it from a predictable source), an attacker
  can pre-mint a session they later share with a victim.
- **Session reuse across tenants.** A server that pools sessions in
  memory by `session_id` only, without `tenant_id` in the lookup key,
  will hand Tenant A's state to Tenant B.
- **Cross-transport session reuse.** If the same session is valid on
  stdio and HTTP+SSE, a stolen `session_id` from a less-protected
  transport escalates.
- **Idle / expiry policy.** A long-lived session that is never
  invalidated allows a captured `session_id` indefinite use.
- **Cancellation race.** `notifications/cancelled` for an in-flight
  request may arrive after the response is partially written.
- **Session-bound caches.** If per-session caches are keyed on
  `session_id` only, two sessions owned by the same tenant but on
  different transports may diverge; if the cache key omits `tenant_id`,
  two tenants can collide.

### (E) Theoretical Attack Surface

- **E-1.** A malicious client **fixates** a `session_id` it knows
  (e.g. generated from a low-entropy source) and lures a victim to use
  the same transport, then resumes the victim's session. →
  `A-SES-001` (session: fixation via predictable IDs).
- **E-2.** A server reuses a `session_id` after restart, causing
  Tenant B to inherit Tenant A's state from a prior run. →
  `A-SES-002` (session: post-restart reuse).
- **E-3.** A session-bound **SSE event queue** is shared across
  tenants because the queue is keyed on `session_id` only. →
  `A-SES-003` (session: cross-tenant event queue).
- **E-4.** A cancellation token from Tenant A is replayed by Tenant
  B to abort Tenant B's request — but the server matches the token
  to the wrong in-flight request. → `A-SES-004` (session:
  cancellation token replay).
- **E-5.** A long-lived session continues to authorize tool calls
  after the principal's token has been **revoked**, because the
  server does not re-check expiry on each request. →
  `A-AUT-007` (auth: post-revocation session continuity).
- **E-6.** A tenant logs out (closes transport) but the server's
  **idle sweeper** is delayed, allowing a co-located attacker to
  resume the session within the grace window. →
  `A-SES-005` (session: idle-window resumption).
- **E-7.** A server uses **sticky session IDs** derived from
  upstream proxy headers, allowing an attacker who controls a header
  to pre-assign session affinity. → `A-SES-006` (session: affinity
  header manipulation).

---

## 7. Context Management & Memory Persistence

### (A) Purpose

Beyond per-request method dispatch, MCP servers commonly retain
**persistent state** that outlives a single request — embeddings of
prior conversations, summaries of tool outputs, cached renderings of
prompt templates, and key-value scratchpads. This persistent state is
the **memory** layer. It is the longest-lived artifact in any
deployment and therefore the most rewarding target for cross-tenant
leakage.

### (B) Internal Workflow

The protocol does not define a memory primitive; persistence is
entirely implementation-defined. Common patterns:

| Pattern | Storage | Key shape | Typical contents |
|---|---|---|---|
| Conversation log | append-only file or DB | `(tenant_id, session_id, ts)` | Full JSON-RPC traffic |
| Tool output cache | Redis / in-process LRU | `(tenant_id, tool_name, args_hash)` | Cached `content` arrays |
| Embedding cache | vector store | `(tenant_id, prompt_hash)` or just `prompt_hash` | Embeddings + metadata |
| Prompt render cache | in-process dict | `(prompt_name, arguments_json)` | Rendered `messages[]` |
| Scratchpad | key-value store | `(tenant_id, key)` | Intermediate handler outputs |

### (C) Data Flow

Cache write path (example — tool-output cache):

```
[tools/call]
    │
    ▼  (handler computes result)
[result content]
    │
    ▼  (cache layer writes: key = (tenant_id, tool_name, hash(args)), value = result)
[persistent store]
    │
    ▼  (next call with same key returns cached value without re-running handler)
[tools/call response from cache]
```

### (D) Inherent Security Implications

- **Cache key without tenant.** A key like `(tool_name, hash(args))`
  collides across tenants whenever two tenants call the same tool with
  the same arguments.
- **Embedding cache without tenant.** Embeddings are typically keyed on
  `prompt_hash`; an attacker can craft a prompt that hashes to the
  same bucket as a target tenant's prompt.
- **Long TTL.** Persistent stores may retain data for days.
- **No protocol-level cache invalidation.** Compromise of a cached
  entry cannot be undone via the protocol.
- **Memory dumps.** Process memory dumps leak cached values verbatim.
- **Conversation log injection.** Append-only logs are an indirect
  injection source.
- **Embedding inversion.** Embeddings can be partially inverted to
  recover the source text (background literature, not MCP-specific;
  flagged for verification).

### (E) Theoretical Attack Surface

- **E-1.** Tenant B calls a tool with arguments identical to Tenant
  A's and **receives Tenant A's cached output**. →
  `A-CCH-003` (cache: cross-tenant cache hit on missing tenant_id).
- **E-2.** A malicious tenant pre-computes an embedding that
  **collides** with Tenant A's prompt hash and reads the neighbour's
  cached embedding. → `A-CCH-004` (cache: embedding collision
  attack).
- **E-3.** A tool handler writes a value to memory with a **shared
  scratchpad key**; another tenant reads it because the key omits
  `tenant_id`. → `A-MEM-002` (memory: cross-tenant scratchpad).
- **E-4.** A server's **conversation log** is world-readable; an
  attacker reads Tenant A's full conversation history from the file
  system. → `A-MEM-003` (memory: log file disclosure).
- **E-5.** A server's embedding store retains **PII** that flows
  through the embedding pipeline; the embedding cache is queryable by
  anyone with API access. → `A-MEM-004` (memory: embedding-store PII
  persistence).
- **E-6.** A server caches a **rendered prompt** whose arguments
  contained Tenant A's tool result; the cached rendering is later
  served to Tenant B because the cache key is `(prompt_name,
  args_hash)` only. → `A-CCH-005` (cache: rendered-prompt
  cross-tenant reuse).
- **E-7.** A container **memory snapshot** taken before garbage
  collection captures another tenant's cached state; the snapshot
  is exfiltrated. → `A-MEM-005` (memory: process snapshot
  exfiltration).

---

## 8. Multi-Client to Single-Server Concurrency

### (A) Purpose

A single MCP server typically serves **many concurrent clients** —
multiple tenants, multiple agents per tenant, and multiple parallel
requests per agent. Concurrency primitives (locks, queues, worker
pools, async tasks, thread pools) determine whether shared mutable
state is correctly partitioned across these clients. Concurrency bugs
are a frequent root cause of cross-tenant leakage: a contextvar
captured in the wrong task, a lock held across tenants, or a queue
that mixes messages from multiple principals.

### (B) Internal Workflow

Common concurrency patterns in reference MCP servers:

| Pattern | Shape | Tenant-isolation property |
|---|---|---|
| asyncio + contextvars | Per-task `ContextVar` carries `tenant_id` | Strong only if no `asyncio.gather` interleaves tasks without preserving context |
| Thread pool | Per-thread local storage | Strong only if the worker is bound to the request that scheduled it |
| Process pool | OS-level isolation | Strong unless IPC channel leaks context |
| Shared queue | Single FIFO across all clients | Insecure by default; tenant must be tagged at enqueue and dequeue |
| Lock per resource | `Lock` keyed on resource URI | Strong only if the key includes `tenant_id` |
| Global lock | One `Lock` for the server | Serialises everything; tenant correctness requires careful context propagation |

### (C) Data Flow

A typical asyncio request handler:

```
[request arrives on transport]
    │
    ▼  (transport reader pushes onto inbound queue)
[server.dispatch()]
    │
    ├──► authenticate(token) -> principal
    ├──► bind principal to current_task via ContextVar
    ├──► handler = tool_registry[params.name]
    └──► result = await handler(**params.arguments)
            │
            ▼  (handler may await other tools; context must propagate)
        [result]
            │
            ▼  (sanitise, log, cache)
        [response]
```

### (D) Inherent Security Implications

- **ContextVar loss across `await`.** A handler that does
  `principal = principal_var.get()` and then awaits without re-binding
  can pick up a different tenant's principal in the resumed task.
- **Race conditions on shared state.** If a tool updates a shared
  structure without proper locking, the update may apply to the wrong
  tenant.
- **Worker pool reuse.** A worker that retained state from a previous
  request leaks prior-tenant data.
- **Cancellation propagation.** Cancelling one tenant's task may
  inadvertently cancel another's if cancellation tokens are not
  scoped.
- **Starvation / DoS.** A tenant that floods the queue can starve
  others.
- **Time-of-check / time-of-use.** A pattern that checks tenant
  permission at queue-dequeue and then executes later may execute
  after the tenant has been revoked.

### (E) Theoretical Attack Surface

- **E-1.** A handler binds `principal` to a ContextVar but loses it
  at an `await`, so a subsequent tool call runs with **Tenant B's
  principal** while still using Tenant A's session resources. →
  `A-SES-007` (session: ContextVar loss across await).
- **E-2.** A shared queue dispatches a message **without checking
  the embedded tenant tag**, and the handler runs with the queue-top
  message's payload under the dequeued principal. →
  `A-MEM-006` (memory: shared queue dequeue without tenant check).
- **E-3.** A worker pool retains **thread-local state** across
  requests, so the next request sees the previous tenant's scratchpad.
  → `A-MEM-007` (memory: thread-local residual).
- **E-4.** A lock keyed on `resource_uri` alone allows two tenants
  to **collide on the same lock** for the same URI, creating a
  covert timing channel. → `A-NSP-006` (namespace: lock key
  collision).
- **E-5.** A tenant **floods the queue** with high-priority
  requests, starving other tenants and inducing the server into a
  degraded path that exposes more diagnostics. → `A-MEM-008`
  (memory: queue starvation side-channel).
- **E-6.** A handler checks tenant permission, then awaits an
  external service; the **revocation** arrives during the await and
  the handler completes anyway. → `A-AUT-008` (auth: TOCTOU across
  await).
- **E-7.** A `asyncio.gather` interleaves two tenants' handlers in
  the same task after a misconfigured `TaskGroup`, causing **call
  interleaving**. → `A-TOL-008` (tool: call interleaving via
  TaskGroup misuse).

---

## 9. Official SDK Implementation Nuances

### (A) Purpose

The official MCP SDKs — the `mcp` Python package and the
`@modelcontextprotocol/...` TypeScript packages — implement the
protocol's reference behavior. SDK defaults, helper utilities, and
ergonomic shortcuts *implicitly embed security choices*. Two SDKs that
nominally implement the same protocol may disagree on default
timeouts, transport selection, JSON-RPC error-code mapping,
context-variable propagation, and how `stdio` arguments are parsed.
SDK divergences are a primary source of deployment-time isolation
failures.

### (B) Internal Workflow

Two reference SDKs are publicly maintained:

- **`mcp`** (Python, ≥1.0.0 per `requirements.txt`). Built on `asyncio`,
  `anyio`, `pydantic`, `httpx`.
- **`@modelcontextprotocol/...`** (TypeScript / Node). Built on the
  Node event loop, `zod` for schema validation, `fetch` for HTTP.

Both expose:

- A **client** API: `connect(transport) -> ClientSession`, with
  `list_tools`, `call_tool`, `list_resources`, `read_resource`,
  `list_prompts`, `get_prompt`.
- A **server** API: `Server(builder).add_tool(...)` /
  `add_resource(...)`, `run(transport)`.
- **Transport adapters**: `stdio`, `sse`, `streamable_http`.

### (C) Data Flow

Python SDK server skeleton (reference shape):

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

server = Server("example")

@server.list_tools()
async def list_tools():
    return [...]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    return [...]

async def main():
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())
```

TypeScript SDK server skeleton (reference shape):

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new Server({ name: "example", version: "0.1.0" }, { capabilities: {} });
server.setRequestHandler("tools/list", async () => ({ tools: [...] }));
server.setRequestHandler("tools/call", async (req) => ({ content: [...] }));
const transport = new StdioServerTransport();
await server.connect(transport);
```

### (D) Inherent Security Implications

- **Decorator-based handler binding.** A Python handler bound via
  `@server.call_tool()` is identified by `__name__`; an attacker who
  can register a handler with the same name shadows the original.
  The TypeScript explicit-registration model is less susceptible.
- **`pydantic` vs `zod` validation.** Python's `pydantic` and TS's
  `zod` differ in default strictness: extra fields may be silently
  dropped, retained, or rejected.
- **Default `stdio` framing.** Newline-delimited JSON is convenient
  but cannot carry binary arguments safely.
- **Default logging verbosity.** Python SDK default may log full
  request bodies; TypeScript SDK default may log errors only.
- **Context propagation.** Python's `asyncio` + `contextvars`
  propagation is reliable only if every `await` boundary preserves
  the context.
- **Error-code mapping.** SDKs may map server-defined error codes to
  typed exceptions differently.
- **Async cancellation.** Python `asyncio.CancelledError` and
  TypeScript `AbortSignal` are not interchangeable.

### (E) Theoretical Attack Surface

- **E-1.** A malicious server returns a **non-spec `type` value** in
  a tool result content block, exploiting a lenient Python SDK parser
  that does not validate against the documented enum. →
  `A-TOL-009` (tool: cross-SDK type-confusion).
- **E-2.** A Python handler uses `pydantic` with
  `model_config.extra = "allow"`, so an attacker can smuggle extra
  fields the TypeScript client assumes the server has validated
  away. → `A-TOL-010` (tool: cross-SDK extra-field smuggling).
- **E-3.** A Python SDK server logs full request bodies by default;
  the log file is readable by other tenants on a shared host. →
  `A-TRN-008` (transport: SDK default-log PII leakage).
- **E-4.** A Python handler loses ContextVar binding across an
  unawaited `await`; the TS SDK does not exhibit this because
  closures carry the binding implicitly. →
  `A-SES-008` (session: cross-SDK context loss).
- **E-5.** A TypeScript client built against the `streamable_http`
  transport sends `Content-Length`-prefixed frames; a Python server
  expecting newline-delimited JSON on the same transport receives
  parse errors that surface as `-32700` to the client, which the
  client misinterprets as auth failure. → `A-TRN-009` (transport:
  cross-SDK framing mismatch).
- **E-6.** A Python SDK server treats `notifications/cancelled` as
  best-effort; a TS client that requires deterministic cancellation
  observes phantom completions. → `A-SES-009` (session: cross-SDK
  cancellation semantics).
- **E-7.** A malicious Python SDK handler registers a tool with the
  same `__name__` as a built-in, exploiting the decorator-based
  binding to shadow the original. → `A-NSP-007` (namespace:
  decorator-name shadowing).

---

## Cross-Component Ticket Index

The following forward ticket IDs appear in the appendix. Phase 5 will
materialise each in `docs/04_Attack_Taxonomy.md`.

### Transport (TRN)

- `A-TRN-001` — framing smuggling
- `A-TRN-002` — cleartext disclosure
- `A-TRN-003` — replay / reorder
- `A-TRN-004` — log-channel leakage
- `A-TRN-005` — cross-tenant impersonation via shared stdio worker
- `A-TRN-006` — SSE frame injection
- `A-TRN-007` — process inheritance leakage
- `A-TRN-008` — SDK default-log PII leakage (cross-reference, §9)
- `A-TRN-009` — cross-SDK framing mismatch (cross-reference, §9)

### Session (SES)

- `A-SES-001` — fixation via predictable IDs
- `A-SES-002` — post-restart reuse
- `A-SES-003` — cross-tenant event queue
- `A-SES-004` — cancellation token replay
- `A-SES-005` — idle-window resumption
- `A-SES-006` — affinity header manipulation
- `A-SES-007` — ContextVar loss across await (cross-reference, §8)
- `A-SES-008` — cross-SDK context loss (cross-reference, §9)
- `A-SES-009` — cross-SDK cancellation semantics (cross-reference, §9)

### Namespace (NSP)

- `A-NSP-001` — tool shadowing (cross-reference, §2)
- `A-NSP-002` — resource-template shadowing (cross-reference, §3)
- `A-NSP-003` — prompt-template argument injection (cross-reference, §4)
- `A-NSP-004` — prompt name squatting (cross-reference, §4)
- `A-NSP-005` — authorization bypass via shadow tool (cross-reference, §5)
- `A-NSP-006` — lock key collision (cross-reference, §8)
- `A-NSP-007` — decorator-name shadowing (cross-reference, §9)

### Tool (TOL)

- `A-TOL-001` — result-borne prompt injection
- `A-TOL-002` — schema-confusion argument smuggling
- `A-TOL-003` — cross-tenant context capture
- `A-TOL-004` — type-confusion result
- `A-TOL-005` — handler-mismatch invocation
- `A-TOL-006` — indirect injection via prompt re-rendering (cross-reference, §4)
- `A-TOL-007` — description-channel injection (cross-reference, §4)
- `A-TOL-008` — call interleaving via TaskGroup misuse (cross-reference, §8)
- `A-TOL-009` — cross-SDK type-confusion (cross-reference, §9)
- `A-TOL-010` — cross-SDK extra-field smuggling (cross-reference, §9)

### Resource (RES)

- `A-RES-001` — path traversal across tenants
- `A-RES-002` — URI normalisation bypass
- `A-RES-003` — symlink escape
- `A-RES-004` — subscription cross-tenant leak
- `A-RES-005` — enumeration leakage
- `A-RES-006` — indirect prompt injection via content
- `A-RES-007` — indirect prompt injection via prompt interpolation (cross-reference, §4)

### Memory (MEM)

- `A-MEM-001` — cross-tenant prompt cache re-injection (cross-reference, §4)
- `A-MEM-002` — cross-tenant scratchpad
- `A-MEM-003` — log file disclosure
- `A-MEM-004` — embedding-store PII persistence
- `A-MEM-005` — process snapshot exfiltration
- `A-MEM-006` — shared queue dequeue without tenant check (cross-reference, §8)
- `A-MEM-007` — thread-local residual (cross-reference, §8)
- `A-MEM-008` — queue starvation side-channel (cross-reference, §8)

### Cache (CCH)

- `A-CCH-001` — cross-tenant cache poisoning via tool key (cross-reference, §2)
- `A-CCH-002` — session-token leakage via cache key (cross-reference, §5)
- `A-CCH-003` — cross-tenant cache hit on missing tenant_id
- `A-CCH-004` — embedding collision attack
- `A-CCH-005` — rendered-prompt cross-tenant reuse

### Auth (AUT)

- `A-AUT-001` — startup-time prompt injection via session establishment (cross-reference, §4)
- `A-AUT-002` — token replay across transports
- `A-AUT-003` — cross-deployment token reuse
- `A-AUT-004` — token forwarding via SSRF
- `A-AUT-005` — capability negotiation spoofing
- `A-AUT-006` — mTLS SAN spoofing
- `A-AUT-007` — post-revocation session continuity (cross-reference, §6)
- `A-AUT-008` — TOCTOU across await (cross-reference, §8)
