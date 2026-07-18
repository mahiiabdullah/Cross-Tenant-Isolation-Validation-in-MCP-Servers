# 04 — Prompts & Context Injection Mechanisms

> Phase 1, Component 4 of 9. Every (E) bullet references a forward ticket ID
> of the form `A-{boundary}-{nnn}`; Phase 5 will resolve these IDs in
> `docs/04_Attack_Taxonomy.md`.

## (A) Purpose

The MCP **Prompts** primitive is a server-managed template that the client
(client application) renders into a string and inserts into the model's
context window. Prompts are *how* servers inject structured guidance
(system messages, tool-use instructions, contextual data) into the model.
Because the resulting string becomes part of the model's input, prompts are
the most direct route for **in-band context injection** — both legitimate
and malicious.

## (B) Internal Workflow

Primary methods:

- `prompts/list` — enumerate prompt templates.
- `prompts/get` — fetch a rendered prompt given a name and arguments.
- `notifications/prompts/list_changed` — server-pushed change notification
  (spec section requires empirical verification).

A prompt template (spec section requires empirical verification for
canonical schema; the following reflects public documentation):

```json
{
  "name": "summarise_document",
  "description": "Summarise a document for the user.",
  "arguments": [
    {"name": "doc_uri", "required": true, "description": "Resource URI to summarise."}
  ]
}
```

`prompts/get` request:

```json
{
  "jsonrpc": "2.0",
  "id": 21,
  "method": "prompts/get",
  "params": {
    "name": "summarise_document",
    "arguments": {"doc_uri": "file:///tenant-a/docs/x.md"}
  }
}
```

`prompts/get` response:

```json
{
  "jsonrpc": "2.0",
  "id": 21,
  "result": {
    "description": "Summarise a document for the user.",
    "messages": [
      {
        "role": "user",
        "content": {
          "type": "text",
          "text": "Please summarise the document at file:///tenant-a/docs/x.md."
        }
      }
    ]
  }
}
```

Ordering / lifecycle constraints:

1. The client decides *when* to call `prompts/get`; the protocol does not
   mandate automatic injection.
2. Rendered prompts become part of the model's context window at the
   discretion of the client host application.
3. Prompt arguments are typically derived from client-side state (user
   input, tool results, resource contents) — creating indirect injection
   opportunities.

## (C) Data Flow

Template variables flow through three trust boundaries before they reach
the model:

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

Each arrow is an attacker-controlled join point when any of the upstream
inputs originate from a tenant other than the requesting one.

The data flow interacts with several MCP surfaces simultaneously:

- **Tool results** are an indirect injection source — tool output becomes
  model context after the client renders it.
- **Resource contents** are an indirect injection source — `resources/read`
  blobs can be embedded in subsequent prompts.
- **Cached embeddings** of prior prompts can be re-fetched and re-injected.

## (D) Inherent Security Implications

- **No content trust marker.** The `messages[].content` envelope has no
  field that says "this text came from a tenant other than the requester."
  The model has no way to distinguish prompt-template text from user text
  from tool-result text.
- **Indirect injection is in-band.** When a prompt template interpolates a
  resource URI or a tool result, the resulting text becomes a covert
  channel between tenants. No protocol-level marker prevents this.
- **Prompt name squatting.** A server may register a prompt whose name
  collides with a built-in or with a prompt another tenant's automation
  fetches automatically.
- **Argument smuggling.** A prompt template may concatenate arguments into
  the rendered text without quoting, enabling injection of arbitrary
  model-facing content via crafted argument values.
- **Auto-injection by host.** Hosts that auto-call `prompts/get` on
  startup create a code-execution-like channel: any prompt the server
  serves runs at startup.
- **No origin audit.** The protocol does not require the rendered prompt
  to record which template and which arguments produced it; downstream
  debugging is impossible without server-side logging.

## (E) Theoretical Attack Surface

- **E-1.** A malicious server (or a tenant who controls a tool result)
  embeds instructions inside a tool output that is later rendered into a
  prompt template, achieving **indirect prompt injection** across
  tenants. → `A-TOL-006` (tool: indirect injection via prompt
  re-rendering; cross-referenced).
- **E-2.** A prompt template uses **unsafe string interpolation** on an
  argument value, letting the caller break out of the intended context
  block and inject a new role (`system: ...`). →
  `A-NSP-003` (namespace: prompt-template argument injection).
- **E-3.** A tenant registers a prompt name that **shadows** a built-in
  (`/help`, `/system`) so the host auto-renders the attacker-controlled
  text. → `A-NSP-004` (namespace: prompt name squatting).
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
  establishment; cross-referenced).
- **E-7.** A prompt template's `description` field contains instructions
  the host mistakenly renders into the model's context, e.g. a UI that
  displays the description as guidance text. → `A-TOL-007` (tool/prompt:
  description-channel injection).

All ticket IDs reference forward entries in
`docs/04_Attack_Taxonomy.md` and will be materialised by Phase 5.
