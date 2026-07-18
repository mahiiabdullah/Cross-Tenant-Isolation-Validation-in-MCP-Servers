# 13 — Tool Confusion (Routing Ambiguity)

> Concept 13 of 14.
> rubric. Concept coverage: **Logic** macro-category.

## (A) Formal Definition

**Tool confusion** is a class of failures in which the system
resolves a tool invocation to the wrong handler because of
ambiguity in the routing logic — typically because multiple tools
share names, share schemas, or are selected on insufficient
criteria. Tool confusion is closely related to but distinct from
the *confused deputy* problem (Concept 14): confused deputy
requires an external principal who is misled; tool confusion can
arise purely from internal logic bugs.

Closest canonical references:

- **CWE-441 Unintended Proxy or Intermediary ('Confused Deputy')** —
  adjacent; covers the variant where the system itself acts as the
  confused deputy (see Concept 14).
- **CWE-1007 Insufficient Visual Distinction of Homoglyphs
  Presenting to User** — covers the user-facing variant where
  visually-similar names cause confusion.
- **CWE-1284 Improper Validation of Specified Quantity in Input** —
  covers input-validation variants that contribute to tool
  confusion.

## (B) Threat Model

- **Attacker position.** A tenant who can register or claim tool
  names that collide with existing tools; a tenant who can craft
  arguments that satisfy the dispatch heuristic of a different
  tool.
- **Assets.** The integrity of the model's dispatch decisions; the
  data accessible through the wrongly-dispatched handler.
- **Preconditions.** (i) Tool names are not uniquely scoped.
  (ii) Dispatch logic uses insufficient criteria (e.g. exact-name
  match without scope). (iii) Tool schemas are not validated
  strictly.

## (C) Real-World / Theoretical Example

An MCP server registers two tools with overlapping names:
`read_file` (built-in, opens files within the tenant root) and
`read_file_backup` (tenant-registered, opens any file on the
host). The model's `tools/list` response includes both, but the
description of `read_file_backup` is more salient. The model
chooses `read_file_backup`, granting the attacker tenant read
access outside the tenant root.

## (D) Standard Defenses

- **Strict name equality.** Names must match exactly; no fuzzy
  matching.
- **Reserved-name registry.** Built-in names cannot be claimed.
- **Schema validation.** Strict `inputSchema` validation rejects
  ambiguous arguments.
- **Single dispatch per name.** The server rejects tool
  registration if the name is already in use.
- **Display-name vs. internal-name separation.** The model sees a
  display name; the server keys on the internal name.

## (E) Open Research Problems

- **Schema-flexibility attacks.** A handler that accepts additional
  properties beyond the declared `inputSchema` allows the caller
  to pass values the dispatch logic does not consider.
- **Description-channel hijacking.** A tool's `description` field
  is the primary signal the model uses for selection; an attacker
  who can edit descriptions hijacks model routing.
- **Cross-tool data flow.** A tool whose output is interpreted as
  another tool's input can become a confused-deputy chain.

## (F) Direct Relation to MCP Architecture

- **MCP boundary.** `namespace`, `tool`.
- **MCP primitive.** `tools/list`; `tools/call`; per-tool
  `inputSchema`.
- **Phase-1 ticket cross-references.**
  - `A-NSP-001` — tool shadowing (a confusion case).
  - `A-TOL-005` — handler-mismatch invocation (a confusion case).
- **Source.** `docs/notes/mcp_learning/02_tools_routing.md` §D–E,
  `09_sdks.md` §D–E.