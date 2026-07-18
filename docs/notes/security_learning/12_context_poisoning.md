# 12 — Context Poisoning

> Phase 2, Concept 12 of 14. Per `prompts/02_security_learning.md` A–F
> rubric. Concept coverage: **Logic** macro-category.

## (A) Formal Definition

**Context poisoning** is the deliberate manipulation of a model's
persistent context — its conversation history, retrieved documents,
cached tool results, embeddings, or scratchpads — to cause future
model behavior to diverge from the developer's intent. Context
poisoning is the *persistent* counterpart of prompt injection
(Concepts 01, 02): injection is ephemeral (a single turn),
poisoning is durable (effects persist across turns or sessions).

There is no CWE specifically for context poisoning as of this
writing; the closest analogues are:

- **CWE-501 Trust Boundary Violation** — the structural pattern of
  untrusted state crossing into trusted logic.
- **CWE-915 Improperly Controlled Modification of Dynamically-
  Determined Object Attributes** — covers state-manipulation
  patterns.
- **MITRE ATLAS AML.T0024 "Exploit ML Model Inference"** — adjacent
  but oriented at the model itself rather than the surrounding
  context.

Academic references for related work include the literature on
*data poisoning* (Biggio et al., "Poisoning Attacks against
Support Vector Machines", 2012 and follow-up work). Whether the
specific application to LLM context windows has a canonical
citation requires empirical verification.

## (B) Threat Model

- **Attacker position.** A tenant who can write to shared state
  (cache, scratchpad, embedding store) that the model later reads
  in another tenant's session; a tenant who can plant content the
  model's retrieval-augmented generation will pick up.
- **Assets.** The integrity of any tenant's session that reads the
  poisoned state.
- **Preconditions.** (i) The cache / scratchpad / embedding store
  lacks a tenant prefix. (ii) The model reads state without
  provenance checks.

## (C) Real-World / Theoretical Example

A multi-tenant MCP server caches rendered prompt templates under
keys `(prompt_name, sha256(args))`. Tenant A crafts a prompt
template with arguments that produce the same hash as a template
Tenant B will request. Tenant A's crafted template contains
attacker instructions. Tenant B later requests a template with
identical arguments; the cache hit serves Tenant A's template. The
model in Tenant B's session now executes Tenant A's instructions.
This is a context-poisoning attack against Tenant B.

## (D) Standard Defenses

- **Tenant-prefixed cache keys.** All cache keys include
  `tenant_id`.
- **Provenance tags.** Every cached value carries a
  `(tenant_id, principal_id, timestamp)` tag; readers verify the
  tag before use.
- **Cache invalidation on principal change.** When the principal
  changes (e.g. token rotation), invalidate session-bound caches.
- **No shared embeddings.** Embedding indices are partitioned per
  tenant.

## (E) Open Research Problems

- **Long-range poisoning.** A poisoned cache entry can persist for
  the cache's TTL — hours, days, or forever. Detection is hard
  because the poisoned value looks normal.
- **Embedding-based poisoning.** An attacker who can write to an
  embedding index can steer nearest-neighbour retrieval toward
  attacker-chosen content even when no string match exists.
- **Composability with indirect injection.** A poisoned cache entry
  can be triggered by an indirect-injection payload, creating a
  multi-step attack.

## (F) Direct Relation to MCP Architecture

- **MCP boundary.** `memory`, `cache`, `tool`.
- **MCP primitive.** Cached tool outputs; cached rendered prompts;
  embedding indices; scratchpads.
- **Phase-1 ticket cross-references.**
  - `A-MEM-001` — cross-tenant prompt cache re-injection.
  - `A-MEM-002` — cross-tenant scratchpad.
  - `A-CCH-001` — cache poisoning via tool key.
  - `A-CCH-005` — rendered-prompt cross-tenant reuse.
- **Source.** `docs/notes/mcp_learning/07_context_memory.md` §D–E,
  `04_prompts_context.md` §E.