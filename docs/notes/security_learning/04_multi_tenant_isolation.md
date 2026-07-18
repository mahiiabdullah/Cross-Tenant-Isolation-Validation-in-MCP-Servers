# 04 — Multi-Tenant Isolation

> Phase 2, Concept 4 of 14. Per `prompts/02_security_learning.md` A–F
> rubric. Concept coverage: **Isolation** macro-category.

## (A) Formal Definition

**Multi-tenant isolation** is the property that distinct *tenants*
(logical principals, organisations, or accounts) sharing a single
deployment of a software system cannot observe, influence, or
consume each other's data, state, or capabilities. In the classical
multi-tenant SaaS literature (Salesforce, ServiceNow, AWS) the
property is decomposed into:

- **No cross-tenant data visibility** — Tenant A cannot read Tenant
  B's data.
- **No cross-tenant influence** — Tenant A cannot modify Tenant B's
  state.
- **No cross-tenant interference** — Tenant A's actions cannot
  degrade Tenant B's service (DoS-as-isolation-failure).
- **No covert channel** — Tenant A cannot infer Tenant B's
  properties through timing, error rates, or resource exhaustion.

There is no single CWE for the general property. Closest analogues
include **CWE-668 Exposure of Resource to Wrong Sphere**, **CWE-1228
API for Service Disruption**, and the broader literature on
multi-tenant cloud isolation. A canonical reference is the NIST
SP 500-299 (Cloud Computing Reference Architecture) and the AWS
Well-Architected Framework "Security" pillar (specific revision
requires empirical verification).

## (B) Threat Model

- **Attacker position.** A tenant with legitimate access to a subset
  of system capabilities; a co-located tenant whose requests share
  transport, process, memory, cache, or storage with the victim's.
- **Assets.** The victim's data (PII, credentials, business data);
  the victim's session state; the victim's resource availability.
- **Preconditions.** Multiple tenants share at least one
  implementation resource (process, host, kernel, network namespace,
  database, cache, queue).

## (C) Real-World / Theoretical Example

Two tenants (A and B) of a shared MCP server each register a `scratch`
key-value scratchpad. Tenant A writes `{"key": "u", "value": "..."}`.
Tenant B, expecting an empty namespace, reads `u` and receives
Tenant A's value because the server keyed the scratchpad on key alone
without a tenant prefix. This is a textbook multi-tenant isolation
failure.

## (D) Standard Defenses

- **Tenant prefix everywhere.** Every key, identifier, queue, and
  table includes the tenant identifier.
- **Defense in depth.** Apply isolation at multiple layers:
  transport (separate connections), session (separate state),
  namespace (separate tool registries), memory (separate stores),
  cache (separate key prefixes), and storage (separate schemas).
- **Resource quotas.** CPU, memory, IOPS, and concurrency caps per
  tenant to bound cross-tenant interference.
- **Capability-based access.** Authorisation is granted per
  (principal, resource) tuple rather than per role.
- **Independent failure domains.** Tenant A's crash or hang must not
  propagate to Tenant B.

## (E) Open Research Problems

- **Composability.** Isolation guarantees often compose
  multiplicatively (each missing boundary multiplies the leakage
  probability); most empirical work studies one boundary at a time.
- **Measurement.** Leakage metrics are usually qualitative
  ("Tenant A observed Tenant B's tool result") rather than
  quantitative.
- **Long-tail interference.** Subtle interactions (timing,
  garbage-collection, scheduling) are hard to reason about
  statically.

## (F) Direct Relation to MCP Architecture

- **MCP boundary.** *All eight boundaries.* Multi-tenant isolation is
  the *meta-property* of the framework: each of the 8 boundaries
  carries an instance of "isolation must be enforced per tenant."
- **MCP primitive.** Every method. Every JSON-RPC envelope is a
  candidate for tenant attribution; every cache key is a candidate
  for tenant scoping.
- **Phase-1 ticket cross-reference.** Every ticket in the
  `A-{prefix}-{nnn}` index (see `docs/notes/mcp_learning/00_appendix.md`)
  is an instance of multi-tenant isolation failure at a specific
  boundary.
- **Source.** All nine Phase-1 component files.
