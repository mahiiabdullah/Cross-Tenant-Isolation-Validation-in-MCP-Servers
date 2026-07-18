# 06 — Resource & Memory Isolation

> Phase 2, Concept 6 of 14. Per `prompts/02_security_learning.md` A–F
> rubric. Concept coverage: **Isolation** macro-category.

## (A) Formal Definition

**Resource and memory isolation** is the property that server-side
*storage* of data — files, blobs, key-value stores, caches,
embedding indices, conversation logs, scratchpads — is partitioned
such that no tenant can read or write another tenant's storage.
Closely related to namespace isolation (Concept 05) but distinguished
by the persistence and storage dimension: namespace isolation governs
*names*; resource / memory isolation governs *bytes*.

Canonical security references include:

- **CWE-552 Files or Directories Accessible to External Parties** —
  classic file-system resource leakage.
- **CWE-538 Insertion of Sensitive Information into Externally-Accessible
  File or Directory** — the insertion counterpart.
- **CWE-922 Insecure Storage of Sensitive Information** — storage
  without proper isolation.
- **CWE-200 Exposure of Sensitive Information to an Unauthorized
  Actor** — the disclosure-side abstraction.

Database-side analogues are captured in **CWE-1295 Debug Messages
Reveal Unnecessary Information** and OWASP A01:2021 / A04:2021 in
the broader Top 10.

## (B) Threat Model

- **Attacker position.** A tenant with read access to the shared
  storage layer (via a tool, an indirect path, or a misconfigured
  ACL); an attacker who can write to the storage layer to plant
  payloads read by other tenants.
- **Assets.** All persistent state: stored tool outputs, embeddings,
  conversation logs, file-system roots, scratchpad values.
- **Preconditions.** (i) Storage is keyed without `tenant_id`. (ii)
  File roots are concatenated naively. (iii) Embeddings are stored in
  a global index without per-tenant namespacing.

## (C) Real-World / Theoretical Example

A shared Redis cache stores tool outputs under keys
`{tool_name}:{sha256(arguments)}`. Tenant A calls `search_docs` with
the same arguments as Tenant B. Tenant B's cached output is served
to Tenant A, who reads Tenant B's search results (which may contain
PII from Tenant B's documents). The cache key lacks a `tenant_id`
component; this is a resource isolation failure.

## (D) Standard Defenses

- **Tenant-prefixed keys.** `{tenant_id}:{tool_name}:{sha256(args)}`.
- **Per-tenant stores.** Each tenant gets a separate database schema,
  S3 prefix, vector index, or file root.
- **Read-after-write consistency per tenant.** Strict consistency
  boundaries within a tenant's namespace; no cross-tenant
  consistency guarantees.
- **Storage-level ACLs.** File permissions / bucket policies / row-
  level security enforced at the storage layer.
- **Encryption per tenant.** Tenant-specific KEKs encrypt stored
  blobs; cross-tenant key access is impossible.

## (E) Open Research Problems

- **Embedding inversion.** Embeddings can be partially inverted to
  recover source text in known-domain attacks (background
  literature; MCP-specific impact requires empirical verification).
- **Cache stampede.** A high-cardinality cache hit can leak
  frequency / existence information across tenants.
- **Long-TTL retention.** Persistent stores with long TTLs retain
  historical data indefinitely; a future breach re-opens all
  historical leakage.

## (F) Direct Relation to MCP Architecture

- **MCP boundary.** `resource`, `memory`, `cache`.
- **MCP primitive.** `resources/read` (file/blob resolution);
  memory stores (implementation-defined); caches (implementation-
  defined); embeddings (implementation-defined).
- **Phase-1 ticket cross-references.**
  - Resource: `A-RES-001` through `A-RES-007`.
  - Memory: `A-MEM-002` (cross-tenant scratchpad),
    `A-MEM-003` (log file disclosure), `A-MEM-004` (embedding-store
    PII persistence), `A-MEM-005` (process snapshot exfiltration),
    `A-MEM-006`, `A-MEM-007`, `A-MEM-008`.
  - Cache: `A-CCH-001` (cache poisoning via tool key),
    `A-CCH-002` (session-token leakage via cache key),
    `A-CCH-003` (cache hit on missing tenant_id),
    `A-CCH-004` (embedding collision), `A-CCH-005` (rendered-prompt
    cross-tenant reuse).
- **Source.** `docs/notes/mcp_learning/03_resources.md` §D–E,
  `07_context_memory.md` §D–E, `08_concurrency.md` §E.
