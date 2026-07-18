# 03 — Tool Injection (Malicious / Shadow Tools)

> Phase 2, Concept 3 of 14. Per `prompts/02_security_learning.md` A–F
> rubric. Concept coverage: **Injection** macro-category.

## (A) Formal Definition

**Tool injection** is the introduction of a tool into the model's
tool registry that the developer did not intend to expose, or the
*shadowing* of a legitimate tool by a same-named or visually similar
entry that routes the model's invocation to attacker-controlled
handler logic. Tool injection is canonised in OWASP LLM Top 10 for
LLM Applications as **LLM05:2025 Improper Supply Chain Management**
(in the broader sense of unauthorised tool / model additions) and
adjacent categories including **LLM07:2025 Insecure Plugin Design**
(in the legacy OWASP framing). Specific OWASP categories and IDs
require empirical verification against the current revision.

Tool injection has two operational modes:

1. **Unauthorised addition** — a tool the developer never registered
   appears in `tools/list`.
2. **Shadowing** — a tool whose name collides with a built-in
   (`read_file`, `exec`, `shell`, `system`) takes precedence in the
   model's dispatch table.

## (B) Threat Model

- **Attacker position.** A malicious tenant who can register tools
  (e.g. via a server-side dynamic plugin loader); a malicious MCP
  server that exposes attacker handlers under common tool names; a
  compromised upstream registry that serves poisoned tool metadata.
- **Assets.** The model's dispatch decisions; downstream actions of
  the chosen tool handler; the host's namespace assumptions.
- **Preconditions.** (i) The server allows dynamic tool registration
  by untrusted parties. (ii) The dispatch logic does not verify tool
  origin. (iii) The model selects tools by name only, without
  per-tenant namespace partitioning.

## (C) Real-World / Theoretical Example

A multi-tenant MCP server allows tenants to register custom tools via
a `POST /admin/tools` endpoint. Tenant X registers a tool named
`exec` that calls `subprocess.run(args)` with the supplied arguments.
Tenant Y then invokes the model, asking "list the contents of the
current directory." The model resolves `exec` to Tenant X's handler,
which runs arbitrary shell commands. Tenant X's tool injection has
trivially become remote code execution in Tenant Y's session.

## (D) Standard Defenses

- **Static tool registries.** The server ships with a frozen, signed
  manifest of allowed tools; runtime registration is disabled.
- **Namespace partitioning.** Tools are namespaced per tenant
  (`tenant_x:exec`); the model's dispatch logic prepends the
  principal's namespace.
- **Built-in reserved names.** A reserved-name registry (`exec`,
  `system`, `__proto__`) cannot be shadowed by tenant-registered
  tools.
- **Plugin review.** Runtime registration requires admin review and
  cryptographically-signed manifests.

## (E) Open Research Problems

- **Polymorphic shadowing.** A tool whose name is a Unicode
  confusable of a built-in (`еxec` with a Cyrillic `е`) bypasses
  string equality checks.
- **Description-channel injection.** A legitimate tool whose
  `description` field contains instructions that re-route the model
  to a different tool on next call.
- **Tool confusion in multi-agent orchestration.** Two agents
  independently register tools; an orchestrator that merges
  registries must enforce namespace uniqueness.

## (F) Direct Relation to MCP Architecture

- **MCP boundary.** `namespace`, `auth`.
- **MCP primitive.** `tools/list` (registry discovery); `tools/call`
  (dispatch).
- **Phase-1 ticket cross-references.**
  - `A-NSP-001` — tool shadowing: a server registers a tool under a
    name that shadows a built-in (`read_file`, `exec`, `shell`); a
    confused-deputy call reaches the wrong handler.
  - `A-NSP-007` — decorator-name shadowing: a Python SDK handler
    registers a tool with the same `__name__` as a built-in,
    exploiting decorator-based binding.
- **Source.** `docs/notes/mcp_learning/02_tools_routing.md` §D–E,
  `09_sdks.md` §D–E.
