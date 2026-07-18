# 09 — Capability-Based Security

> Concept 9 of 14.
> rubric. Concept coverage: **Architecture** macro-category.

## (A) Formal Definition

**Capability-based security** is an access-control model in which
*capabilities* — unforgeable tokens of authority — are the sole
mechanism by which a subject obtains access to an object. A
capability is a tuple `(object, rights)` that the holder can
present to gain access; capabilities cannot be forged, copied, or
amplified without the holder's cooperation.

The classical references are:

- **Dennis & Van Horn, "Programming Semantics for Multiprogrammed
  Computations" (CACM 1966)** — the foundational capability paper.
- **Levy, "Capability-Based Computer Systems" (1984)** — book-length
  treatment.
- **Miller, Yee, Shapiro, and the E / Capsicum communities** —
  modern operating-system instantiations (Capsicum was added to
  FreeBSD 9.0 in 2012).

In modern web / agentic contexts, capability-based security is
closely related to OAuth 2.0 scopes (Concept 10) and to
macaroons / biscuits (Google Research, Birgisson et al. 2014).

## (B) Threat Model

- **Attacker position.** A subject who has been delegated a
  capability for some purpose; an attacker who attempts to
  forge, copy, or amplify capabilities beyond what was delegated.
- **Assets.** The objects whose access is governed by capabilities.
- **Preconditions.** (i) The system mints capabilities without
  unforgeability. (ii) Capabilities can be copied or amplified
  (no confinement). (iii) The capability check is not enforced
  consistently.

## (C) Real-World / Theoretical Example

An MCP server issues each tenant a *capability* token that
encodes `(tenant_id, allowed_tools, allowed_resources, expiry)`.
The token is signed with a server-side key; the server validates
the signature on every request. A tenant who captures another
tenant's token cannot use it because the token is bound to the
holder's identity (e.g. via mTLS) and the server rejects identity
mismatches. This is capability-based security applied to MCP.

## (D) Standard Defenses

- **Cryptographic capabilities.** Sign capabilities with a key the
  holder cannot access.
- **Confinement.** A capability holder cannot delegate beyond the
  rights they hold (no amplification).
- **Attenuation.** A capability can be downgraded (e.g. read-only)
  for delegation without losing provenance.
- **No ambient authority.** Subjects acquire no access by default;
  every access is capability-mediated.
- **Revocation.** Capabilities support revocation by serial-number
  lookup or by short TTLs.

## (E) Open Research Problems

- **Revocation at scale.** Distributed systems have bounded
  revocation latency; long-lived capabilities create a window of
  vulnerability.
- **Composability.** Composing capabilities across federated
  systems (multi-cloud, multi-org) is non-trivial.
- **Capability-protected AI agents.** Agents that autonomously
  acquire, attenuate, and pass capabilities require explicit
  policy frameworks that do not yet exist at MCP layer.

## (F) Direct Relation to MCP Architecture

- **MCP boundary.** `auth`, `namespace`.
- **MCP primitive.** `initialize` (capability negotiation); per-
  method authorisation (capability check on every dispatch).
- **Phase-1 ticket cross-references.**
  - `A-AUT-005` — capability negotiation spoofing: a malicious
    client advertises capabilities it does not possess.
  - `A-NSP-005` — authorization bypass via shadow tool: a server
    authorizes on `tool_name` but a malicious tenant invokes a
    shadow tool whose name the policy does not list.
- **Source.** `docs/notes/mcp_learning/05_auth.md` §D–E,
  `02_tools_routing.md` §D.