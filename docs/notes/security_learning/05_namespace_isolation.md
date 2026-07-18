# 05 — Namespace Isolation

> Phase 2, Concept 5 of 14. Per `prompts/02_security_learning.md` A–F
> rubric. Concept coverage: **Isolation** macro-category.

## (A) Formal Definition

**Namespace isolation** is the property that the *names* under which
a system stores and retrieves objects (tools, resources, prompts,
configuration keys, file paths, table names, queue names) are
uniquely scoped per tenant such that no tenant can resolve another
tenant's name to an object they should not access.

The classical security references are:

- **CWE-706 Use of Incorrectly-Resolved Name or Reference** — captures
  the failure mode in which a system resolves a name to the wrong
  object due to namespace ambiguity.
- **CWE-1007 Insufficient Visual Distinction of Homoglyphs Presenting
  to User** — adjacent but oriented at user-facing confusion; relevant
  when display names carry authority.
- **CWE-22 Improper Limitation of a Pathname to a Restricted Directory
  ('Path Traversal')** — the file-system specialisation.

A broader reference is RFC 8140 (URI namespaces) and the W3C
"Identifiers" recommendation (specific references require empirical
verification against current revisions).

## (B) Threat Model

- **Attacker position.** A tenant who can register names in the
  shared namespace; a tenant who can craft request inputs whose
  internal references collide with another tenant's names.
- **Assets.** The victim's namespace entries (their tools, resources,
  prompts); the integrity of the victim's name resolution path.
- **Preconditions.** (i) Names are not tenant-prefixed. (ii)
  Resolution does not validate that the resolved object's principal
  matches the requester's principal.

## (C) Real-World / Theoretical Example

Two MCP tenants share a single `resources/list` catalog. Tenant A
registers a resource template
`file:///tenants/{tenant_id}/docs/{doc_id}.md`. Tenant B requests
`file:///tenants/tenant_b/docs/internal.md`; the server's resolver
matches the template, executes the lookup, but Tenant A's
registration is preferred by the registry, returning Tenant A's
doc instead.

## (D) Standard Defenses

- **Per-tenant name prefixes.** `tenant_{id}:tool_name`.
- **Per-tenant sub-trees.** File paths, database schemas, and
  resource URIs are rooted under `tenant_{id}/`.
- **Registry isolation.** Each tenant has a separate tool / resource
  / prompt registry.
- **Reserved-name blocks.** Built-in names (`exec`, `system`,
  `__proto__`) cannot be claimed by tenants.
- **Homoglyph detection.** Names that differ only by Unicode
  confusables are rejected at registration time.

## (E) Open Research Problems

- **Polymorphic collisions.** Names that are visually distinct but
  resolve to the same internal identifier (Unicode normalisation
  forms NFKC vs NFD; case-folding rules; locale-specific collation).
- **Cross-language namespace portability.** Namespaces defined in
  Python's pathlib vs POSIX vs Windows file semantics diverge; an
  MCP server that abstracts over OSes must enforce a single
  canonicalisation.
- **URI vs path.** MCP resources often use URI schemes whose
  semantics (e.g. `postgres://`) differ from file-system semantics.

## (F) Direct Relation to MCP Architecture

- **MCP boundary.** `namespace`.
- **MCP primitive.** `tools/list` / `tools/call`; `resources/list` /
  `resources/templates/list` / `resources/read`; `prompts/list` /
  `prompts/get`.
- **Phase-1 ticket cross-references.**
  - `A-NSP-001` — tool shadowing.
  - `A-NSP-002` — resource-template shadowing.
  - `A-NSP-003` — prompt-template argument injection.
  - `A-NSP-004` — prompt name squatting.
  - `A-NSP-005` — authorization bypass via shadow tool.
  - `A-NSP-006` — lock key collision (cross-reference, §8).
  - `A-NSP-007` — decorator-name shadowing (cross-reference, §9).
- **Source.** `docs/notes/mcp_learning/02_tools_routing.md` §E,
  `03_resources.md` §E, `04_prompts_context.md` §E.
