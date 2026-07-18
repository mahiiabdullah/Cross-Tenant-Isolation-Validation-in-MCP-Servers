# 02 — Tools & Tool Execution Routing

> Phase 1, Component 2 of 9. Every (E) bullet references a forward ticket ID
> of the form `A-{boundary}-{nnn}`; Phase 5 will resolve these IDs in
> `docs/04_Attack_Taxonomy.md`.

## (A) Purpose

The **Tool** primitive is the central capability exposed by an MCP server.
A tool is a named, parameterised function with a JSON-Schema-style input
contract and a structured output. Tool **routing** is the path from a client
issuing `tools/call` to the server-side handler that executes the action
and returns a `content` block. Routing correctness is the prerequisite for
isolating tenants from each other's capabilities: a routing bug that
dispatches a call to the wrong handler is an immediate isolation failure.

## (B) Internal Workflow

Three primary methods:

- `tools/list` — enumerate tool descriptors.
- `tools/call` — invoke a named tool with arguments.
- `notifications/tools/list_changed` — server-pushed notification that the
  tool catalog changed (spec section requires empirical verification for
  whether clients are required to re-list).

Tool descriptor shape (spec section requires empirical verification for the
canonical field set; the following reflects the publicly documented
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

`tools/call` response (text content example):

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "result": {
    "content": [{"type": "text", "text": "...matched docs..."}],
    "isError": false
  }
}
```

Ordering constraints:

1. Clients MUST call `tools/list` before issuing `tools/call` for a name
   they have not seen (spec section requires empirical verification).
2. The server SHOULD validate arguments against `inputSchema`; clients
   SHOULD NOT assume strict server-side validation.
3. Long-running tools MUST respect cancellation tokens via
   `notifications/cancelled` (spec section requires empirical verification).

## (C) Data Flow

Inputs → routing decision → handler execution → structured output:

| Stage | Input | Decision basis | Output |
|---|---|---|---|
| Authenticate | JSON-RPC request | Token / scope check | Authorised call or `-32001`-class error |
| Resolve tool | `params.name` | Internal name table | Handler reference or `-32601` Method not found |
| Validate args | `params.arguments` | `inputSchema` (jsonschema) | Validated args or `-32602` Invalid params |
| Dispatch | Handler invocation | Tenant context bound at session | Result `content` array |
| Sanitise result | Raw handler output | Server-defined policy | `content` array (may be redacted) |

Errors propagate as JSON-RPC error objects (RFC 7455):

| Code | Meaning |
|---|---|
| `-32700` | Parse error |
| `-32600` | Invalid request |
| `-32601` | Method not found |
| `-32602` | Invalid params |
| `-32603` | Internal error |
| `-32000` to `-32099` | Server-defined (implementation-defined codes include auth failures; spec section requires empirical verification) |

## (D) Inherent Security Implications

- **Implicit trust in tool output.** Tool outputs are typically rendered
  back into the model's context window. The protocol does not specify a
  trust marker on returned `content`; the client decides what to do.
- **Schema confusion.** If a tool's `inputSchema` accepts arbitrary
  additional properties, an attacker can smuggle fields the handler
  ignores client-side but interprets server-side (or vice versa).
- **Tool-name squatting.** A server may register a tool whose name
  collides with a built-in or another tenant's preferred tool name. The
  spec does not mandate namespace partitioning by tenant.
- **No result sanitisation requirement.** The protocol does not require
  stripping control characters, ANSI escapes, or hidden instructions from
  `content` before returning them to the client.
- **Side-effecting tools.** Some tools (write to disk, send email, run a
  shell command) have effects outside the protocol. Once called, their
  action is observable only through side channels.
- **Dynamic registration.** Servers may register tools at runtime via
  in-band mechanisms; a compromised agent that triggers registration may
  introduce a tool the host did not intend to expose.

## (E) Theoretical Attack Surface

- **E-1.** A malicious server returns a `content` array whose `text`
  includes **hidden instructions** the model treats as commands (indirect
  prompt injection via tool result). → `A-TOL-001` (tool: result-borne
  prompt injection).
- **E-2.** A tenant crafts a `tools/call` whose `arguments` contain
  **schema-confusing extra fields** that a careless handler
  deserialises. → `A-TOL-002` (tool: schema-confusion argument smuggling).
- **E-3.** A server registers a tool under a name that **shadows** a
  built-in (`read_file`, `exec`, `shell`). A confused-deputy call
  reaches the wrong handler. → `A-NSP-001` (namespace: tool shadowing;
  cross-referenced from tool routing).
- **E-4.** A tenant invokes a tool that **leaks another tenant's
  arguments** from a shared in-memory queue (e.g. an async task that
  captures the wrong context). → `A-TOL-003` (tool: cross-tenant context
  capture).
- **E-5.** A malicious tool handler emits a `content` array with a
  `type` value not in the documented set, exploiting lenient client
  parsers. → `A-TOL-004` (tool: type-confusion result).
- **E-6.** A tool whose description advertises benign behaviour actually
  **dispatches to a side-effecting handler** based on hidden
  `arguments` keys. → `A-TOL-005` (tool: handler-mismatch invocation).
- **E-7.** Tool results are cached by `(tool_name, arguments)` key,
  allowing **cross-tenant cache poisoning** when the key omits
  `tenant_id`. → `A-CCH-001` (cache: cross-tenant cache poisoning via
  tool key; cross-referenced from tool routing).

All ticket IDs reference forward entries in
`docs/04_Attack_Taxonomy.md` and will be materialised by Phase 5.
