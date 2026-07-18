# 07 — Context Management & Memory Persistence

> Phase 1, Component 7 of 9. Every (E) bullet references a forward ticket ID
> of the form `A-{boundary}-{nnn}`; Phase 5 will resolve these IDs in
> `docs/04_Attack_Taxonomy.md`.

## (A) Purpose

Beyond per-request method dispatch, MCP servers commonly retain
**persistent state** that outlives a single request — embeddings of prior
conversations, summaries of tool outputs, cached renderings of prompt
templates, and key-value scratchpads. This persistent state is the
**memory** layer. It is the longest-lived artifact in any deployment and
therefore the most rewarding target for cross-tenant leakage: a memory
entry written by Tenant A and read by Tenant B months later is still a
successful isolation failure.

## (B) Internal Workflow

The protocol does not define a memory primitive; persistence is entirely
implementation-defined. Common patterns include:

| Pattern | Storage | Key shape | Typical contents |
|---|---|---|---|
| Conversation log | append-only file or DB | `(tenant_id, session_id, ts)` | Full JSON-RPC traffic |
| Tool output cache | Redis / in-process LRU | `(tenant_id, tool_name, args_hash)` | Cached `content` arrays |
| Embedding cache | vector store | `(tenant_id, prompt_hash)` or just `prompt_hash` | Embeddings + metadata |
| Prompt render cache | in-process dict | `(prompt_name, arguments_json)` | Rendered `messages[]` |
| Scratchpad | key-value store | `(tenant_id, key)` | Intermediate handler outputs |

The protocol provides no standardised invalidation API; servers typically
rely on TTL or explicit `cache.invalidate` tool calls. Memory state is
not part of the JSON-RPC surface; it is observable only through the
methods that read from it.

## (C) Data Flow

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

Cache read path (example — embedding cache):

```
[prompts/get with arguments]
    │
    ▼  (server computes embedding of arguments)
[query vector store: key = (prompt_hash), value = cached embedding]
    │
    ▼  (returns nearest-neighbour prompts, with their original arguments)
[neighbour prompts whose original arguments may belong to a different tenant]
```

## (D) Inherent Security Implications

- **Cache key without tenant.** The most common bug. A key like
  `(tool_name, hash(args))` collides across tenants whenever two tenants
  call the same tool with the same arguments. The cached value from
  Tenant A is served to Tenant B.
- **Embedding cache without tenant.** Embeddings are typically keyed on
  `prompt_hash`; an attacker can craft a prompt that hashes to the same
  bucket as a target tenant's prompt and exfiltrate the neighbour's
  embedding.
- **Long TTL.** Persistent stores may retain data for days; an attacker
  who compromises the store gets historical cross-tenant data.
- **No protocol-level cache invalidation.** Compromise of a cached entry
  cannot be undone via the protocol; operators must reach into the store.
- **Memory dumps.** Process memory dumps (core files, container
  snapshots) leak cached values verbatim.
- **Conversation log injection.** Append-only logs are an indirect
  injection source: a future process may re-render log entries as
  prompts.
- **Embedding inversion.** Embeddings can be partially inverted to
  recover the source text in known-domain attacks (background literature,
  not MCP-specific; flagged for verification).

## (E) Theoretical Attack Surface

- **E-1.** Tenant B calls a tool with arguments identical to Tenant A's
  and **receives Tenant A's cached output**. →
  `A-CCH-003` (cache: cross-tenant cache hit on missing tenant_id).
- **E-2.** A malicious tenant pre-computes an embedding that **collides**
  with Tenant A's prompt hash and reads the neighbour's cached
  embedding. → `A-CCH-004` (cache: embedding collision attack).
- **E-3.** A tool handler writes a value to memory with a **shared
  scratchpad key**; another tenant reads it because the key omits
  `tenant_id`. → `A-MEM-002` (memory: cross-tenant scratchpad).
- **E-4.** A server's **conversation log** is world-readable; an
  attacker reads Tenant A's full conversation history from the file
  system. → `A-MEM-003` (memory: log file disclosure).
- **E-5.** A server's embedding store retains **PII** (e.g. user
  emails) that flows through the embedding pipeline; the embedding
  cache is queryable by anyone with API access. →
  `A-MEM-004` (memory: embedding-store PII persistence).
- **E-6.** A server caches a **rendered prompt** whose arguments
  contained Tenant A's tool result; the cached rendering is later
  served to Tenant B because the cache key is `(prompt_name,
  args_hash)` only. → `A-CCH-005` (cache: rendered-prompt
  cross-tenant reuse).
- **E-7.** A container **memory snapshot** taken before garbage
  collection captures another tenant's cached state; the snapshot
  is exfiltrated. → `A-MEM-005` (memory: process snapshot
  exfiltration).

All ticket IDs reference forward entries in
`docs/04_Attack_Taxonomy.md` and will be materialised by Phase 5.