# 09 — Official SDK Implementation Nuances

> Phase 1, Component 9 of 9. Every (E) bullet references a forward ticket ID
> of the form `A-{boundary}-{nnn}`; Phase 5 will resolve these IDs in
> `docs/04_Attack_Taxonomy.md`.

## (A) Purpose

The official MCP SDKs — the `mcp` Python package and the `@modelcontextprotocol/...`
TypeScript packages — implement the protocol's reference behavior. SDK
defaults, helper utilities, and ergonomic shortcuts *implicitly embed
security choices*. Two SDKs that nominally implement the same protocol
may disagree on default timeouts, transport selection, JSON-RPC
error-code mapping, context-variable propagation, and how `stdio`
arguments are parsed. SDK divergences are a primary source of
deployment-time isolation failures: a developer who follows the
Python tutorial will build a different security posture than one who
follows the TypeScript tutorial, even against identical traffic.

## (B) Internal Workflow

Two reference SDKs are publicly maintained:

- **`mcp`** (Python, ≥1.0.0 per `requirements.txt`). Built on `asyncio`,
  `anyio`, `pydantic`, `httpx`.
- **`@modelcontextprotocol/...`** (TypeScript / Node). Built on the
  Node event loop, `zod` for schema validation, `fetch` for HTTP.

Both expose:

- A **client** API: `connect(transport) -> ClientSession`, with
  `list_tools`, `call_tool`, `list_resources`, `read_resource`,
  `list_prompts`, `get_prompt`.
- A **server** API: `Server(builder).add_tool(...)` / `add_resource(...)`,
  `run(transport)`.
- **Transport adapters**: `stdio`, `sse`, `streamable_http`.

SDK ergonomics:

- Python: decorators (`@server.list_tools()`, `@server.call_tool()`)
  that bind a coroutine to a JSON-RPC method name.
- TypeScript: explicit registration via `server.setRequestHandler(...)`.

Default behaviors differ:

- Default JSON-RPC request timeout (spec section requires empirical
  verification; both SDKs ship with defaults).
- Default `stdio` framing (newline-delimited JSON in both; UTF-8
  handling differs; spec section requires empirical verification).
- Default `logging` level (Python: `WARNING`; TypeScript: `info`; spec
  section requires empirical verification).
- Default session-id generation (`uuid4().hex[:8]` in the reference
  Python skeleton in `framework/utils/ids.py`; TypeScript default
  requires empirical verification).

## (C) Data Flow

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

Python SDK client skeleton (reference shape):

```python
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

async with stdio_client(command, args) as (r, w):
    async with ClientSession(r, w) as session:
        await session.initialize()
        tools = await session.list_tools()
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

## (D) Inherent Security Implications

- **Decorator-based handler binding.** A Python handler bound via
  `@server.call_tool()` is identified by `__name__`; an attacker who
  can register a handler with the same name (e.g. via dynamic plugin
  loading) shadows the original. The TypeScript explicit-registration
  model is less susceptible.
- **`pydantic` vs `zod` validation.** Python's `pydantic` and TS's
  `zod` differ in default strictness: extra fields may be silently
  dropped, retained, or rejected. Cross-SDK schema-confusion is
  observable.
- **Default `stdio` framing.** Newline-delimited JSON is convenient
  but cannot carry binary arguments safely; embedded newlines in
  arguments require length-prefix framing that SDKs do not implement
  by default (spec section requires empirical verification).
- **Default logging verbosity.** Python SDK default may log full
  request bodies, including tokens. TypeScript SDK default may log
  errors only. Operators must explicitly lower verbosity.
- **Context propagation.** Python's `asyncio` + `contextvars`
  propagation is reliable only if every `await` boundary preserves
  the context. Reference Python tutorials do not always demonstrate
  this; the TypeScript equivalent relies on closures (no contextvar
  analogue).
- **Error-code mapping.** SDKs may map server-defined error codes
  (`-32000` to `-32099`) to typed exceptions differently. A client
  built against one SDK may mishandle errors from a server built
  against another.
- **Async cancellation.** Python `asyncio.CancelledError` and
  TypeScript `AbortSignal` are not interchangeable; a handler that
  raises on cancel in one SDK may not raise in the other.

## (E) Theoretical Attack Surface

- **E-1.** A malicious server returns a **non-spec `type` value** in a
  tool result content block, exploiting a lenient Python SDK parser
  that does not validate against the documented enum. →
  `A-TOL-009` (tool: cross-SDK type-confusion; cross-referenced).
- **E-2.** A Python handler uses `pydantic` with
  `model_config.extra = "allow"`, so an attacker can smuggle extra
  fields the TypeScript client assumes the server has validated
  away. → `A-TOL-010` (tool: cross-SDK extra-field smuggling;
  cross-referenced).
- **E-3.** A Python SDK server logs full request bodies by default;
  the log file is readable by other tenants on a shared host. →
  `A-TRN-008` (transport: SDK default-log PII leakage;
  cross-referenced).
- **E-4.** A Python handler loses ContextVar binding across an
  unawaited `await`; the TS SDK does not exhibit this because
  closures carry the binding implicitly. →
  `A-SES-008` (session: cross-SDK context loss; cross-referenced).
- **E-5.** A TypeScript client built against the `streamable_http`
  transport sends `Content-Length`-prefixed frames; a Python server
  expecting newline-delimited JSON on the same transport receives
  parse errors that surface as `-32700` to the client, which the
  client misinterprets as auth failure. → `A-TRN-009` (transport:
  cross-SDK framing mismatch; cross-referenced).
- **E-6.** A Python SDK server treats `notifications/cancelled` as
  best-effort; a TS client that requires deterministic cancellation
  observes phantom completions. → `A-SES-009` (session: cross-SDK
  cancellation semantics; cross-referenced).
- **E-7.** A malicious Python SDK handler registers a tool with the
  same `__name__` as a built-in, exploiting the decorator-based
  binding to shadow the original. → `A-NSP-007` (namespace:
  decorator-name shadowing; cross-referenced).

All ticket IDs reference forward entries in
`docs/04_Attack_Taxonomy.md` and will be materialised by Phase 5.