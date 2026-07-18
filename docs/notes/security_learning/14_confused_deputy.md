# 14 — Confused Deputy Problem

> Phase 2, Concept 14 of 14. Per `prompts/02_security_learning.md` A–F
> rubric. Concept coverage: **Logic** macro-category.

## (A) Formal Definition

The **confused deputy** is a security failure in which a program
(the *deputy*) that has been delegated authority by one principal
is tricked into using that authority on behalf of a *different*
principal — typically an attacker. The classic reference is
**Hardy, "The Confused Deputy (or why capabilities might have
been invented)"** (ACM SIGOPS Operating Systems Review, 1988),
which uses a compiler cross-compiling for a billing system as the
canonical example.

Closest CWE:

- **CWE-441 Unintended Proxy or Intermediary ('Confused Deputy')** —
  the canonical mapping.
- **CWE-269 Improper Privilege Management** — adjacent.
- **CWE-732 Incorrect Permission Assignment for Critical Resource**
  — adjacent.

In MCP deployments, the deputy is the MCP server (or a tool
handler); the principal is a tenant; the attacker's goal is to
induce the deputy to use the principal's authority on the
attacker's behalf.

## (B) Threat Model

- **Attacker position.** A tenant who can supply inputs to a
  deputy that cause the deputy to use *its* authority (not the
  attacker's) to access a resource.
- **Assets.** The objects the deputy has authority over — typically
  the host file system, the network, or other tenants' data.
- **Preconditions.** (i) The deputy holds authority beyond what
  the requesting tenant holds. (ii) The deputy uses its
  authority, not the caller's authority, to act. (iii) The
  deputy does not verify that the requester is authorised for the
  resulting action.

## (C) Real-World / Theoretical Example

An MCP tool handler has authority to read any file on the host
(file-system authority is held by the server process). A tenant
calls the tool with a filename that escapes the tenant root
(`../../etc/passwd`). The handler reads the file using its own
authority, not the tenant's, and returns the contents to the
tenant. The handler is the confused deputy; the tenant has used
the handler's elevated authority to read a file the tenant should
not be able to access.

## (D) Standard Defenses

- **Authority-based dispatch.** The deputy acts under the
  requester's authority, not its own.
- **Path canonicalisation + tenant scoping.** The deputy resolves
  every path under the tenant root before reading; symlinks and
  `..` segments are rejected.
- **Capability attenuation.** The deputy holds narrowly-scoped
  capabilities; cross-tenant authority is impossible.
- **Auditing.** Every deputy action is logged with the
  requester's principal.
- **Input sanitisation.** All handler inputs are validated against
  a strict schema; ambiguous or malicious inputs are rejected
  before dispatch.

## (E) Open Research Problems

- **Library-level confused deputies.** Third-party libraries that
  hold ambient authority (e.g. database connection pools, file
  handles) become confused deputies by accident; detecting these
  patterns statically is hard.
- **Cross-handler chaining.** When Handler A calls Handler B, B's
  authority may be amplified by A's authority; the resulting
  authority is non-obvious.
- **Confused deputy in multi-agent systems.** Multi-agent
  orchestrations create many deputy relationships; the
  attribution of authority is increasingly opaque.

## (F) Direct Relation to MCP Architecture

- **MCP boundary.** `auth`, `tool`, `resource`.
- **MCP primitive.** `tools/call` (the handler is the deputy);
  `resources/read` (the resource resolver is the deputy).
- **Phase-1 ticket cross-references.**
  - `A-TOL-005` — handler-mismatch invocation (the handler is
    invoked with mismatched authority).
  - `A-AUT-005` — capability negotiation spoofing (the deputy
    negotiates capabilities on behalf of the wrong principal).
  - `A-RES-001` — path traversal across tenants (the resource
    resolver is the confused deputy).
- **Source.** `docs/notes/mcp_learning/02_tools_routing.md` §D–E,
  `03_resources.md` §D–E, `05_auth.md` §D–E.