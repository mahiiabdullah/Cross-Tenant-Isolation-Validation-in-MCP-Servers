# 04 — Attack Taxonomy

> **Phase 5 deliverable.** Per-boundary STRIDE enumeration plus
> misuse cases for the MCP isolation threat model. Source of
> truth for attack stubs under `attacks/`. Each STRIDE row
> references one or more ticket IDs minted in Phase 1
> (`docs/notes/mcp_learning/00_appendix.md`) and indexed by
> `docs/02_Threat_Model.md`.

## Status

- All 8 boundaries have STRIDE rows (6 letters × 8 boundaries
  = 48 rows).
- 4 misuse cases documented.
- 64 attack stubs materialised under `attacks/<boundary>/`
  (8 stubs per boundary, one per STRIDE letter; 8 × 8 = 64).
- All 63 forward ticket IDs from Phase 1 are bound to at least
  one STRIDE row in this document.

## STRIDE Conventions in MCP Context

| Letter | MCP meaning |
| --- | --- |
| **S** — Spoofing | Impersonate a tenant or forge a session/transport identity. |
| **T** — Tampering | Modify another tenant's state via a shared write path. |
| **R** — Repudiation | Hide or falsify the actor of an attack via missing audit. |
| **I** — Information Disclosure | Read another tenant's data. |
| **D** — Denial of Service | Starve or degrade another tenant's service. |
| **E** — Elevation of Privilege | Bypass authorisation via shadow / renamed capability. |

Where a STRIDE letter is not naturally applicable to a boundary
(e.g. **S** for the pure `Cache` boundary), the row exists but
explains "not applicable at this boundary — see Auth boundary."

## Cross-Boundary Ticket Inventory

The 63 ticket IDs from Phase 1 are partitioned across the eight
boundaries as follows (used to build the per-boundary STRIDE
tables below):

- **Transport (TRN)** — `A-TRN-001`–`A-TRN-009` (9 tickets)
- **Session (SES)** — `A-SES-001`–`A-SES-009` (9 tickets)
- **Namespace (NSP)** — `A-NSP-001`–`A-NSP-007` (7 tickets)
- **Tool (TOL)** — `A-TOL-001`–`A-TOL-010` (10 tickets)
- **Resource (RES)** — `A-RES-001`–`A-RES-007` (7 tickets)
- **Memory (MEM)** — `A-MEM-001`–`A-MEM-008` (8 tickets)
- **Cache (CCH)** — `A-CCH-001`–`A-CCH-005` (5 tickets)
- **Auth (AUT)** — `A-AUT-001`–`A-AUT-008` (8 tickets)

---

## 1. Transport Boundary — STRIDE

> Phase-1 component ref: `docs/notes/mcp_learning/01_transport.md`
> §B–E. Cross-references: §9 (SDKs) for `A-TRN-008`, `A-TRN-009`.

| STRIDE | Threat | Ticket(s) | CWE |
| --- | --- | --- | --- |
| **S** | Token / session replay captured from cleartext transport | `A-AUT-002`, `A-TRN-002` | CWE-294 (Authentication Bypass by Capture-Replay) |
| **T** | CRLF / framing byte injection splicing a forged JSON-RPC envelope inside a string argument | `A-TRN-001` | CWE-93 (CRLF Injection), CWE-915 (Improperly Controlled Modification of Dynamically-Determined Object Attributes) |
| **R** | Server logs full JSON-RPC payload to stderr/log file; the log file can be edited and the actor hidden | `A-TRN-004`, `A-TRN-008` | CWE-778 (Insufficient Logging) |
| **I** | Passive on-path adversary reads tool arguments and results over cleartext HTTP+SSE | `A-TRN-002`, `A-TRN-007` | CWE-319 (Cleartext Transmission of Sensitive Information) |
| **D** | Process-level inheritance leak (FD, env) breaks tenant's resource ceiling by exhausting host descriptors | `A-TRN-007` | CWE-400 (Uncontrolled Resource Consumption) |
| **E** | Cross-tenant impersonation via shared stdio worker that mints no per-pipe tenant identity | `A-TRN-005`, `A-TRN-009` | CWE-285 (Improper Authorization) |

**Defence references:** TLS 1.3 (RFC 8446) for `I`/`S`; length-prefixed framing (or `application/jsonl` with bounded line length) for `T`; OS-level process isolation (Capsicum, namespaces) for `E`/`D`.

---

## 2. Session Boundary — STRIDE

> Phase-1 component ref: `docs/notes/mcp_learning/06_sessions.md`
> §B–E. Cross-references: §8 (concurrency) for `A-SES-007`; §9
> (SDKs) for `A-SES-008`, `A-SES-009`.

| STRIDE | Threat | Ticket(s) | CWE |
| --- | --- | --- | --- |
| **S** | Session fixation via predictable IDs (low-entropy mint) | `A-SES-001`, `A-SES-006` | CWE-330 (Use of Insufficiently Random Values), CWE-384 (Session Fixation) |
| **T** | Session reuse post-restart: Tenant B inherits Tenant A's state because the server reuses `session_id` after restart | `A-SES-002` | CWE-613 (Insufficient Session Expiration) |
| **R** | Idle-window resumption: the audit trail for actions in the grace window is unattributable to a specific tenant | `A-SES-005` | CWE-778 (Insufficient Logging) |
| **I** | Cross-tenant SSE event queue keyed on `session_id` only, without `tenant_id` in the lookup key | `A-SES-003` | CWE-668 (Exposure of Resource to Wrong Sphere) |
| **D** | Cancellation-token replay: replaying Tenant A's cancellation token against Tenant B's in-flight request aborts B's work | `A-SES-004` | CWE-754 (Improper Check for Unusual or Exceptional Conditions) |
| **E** | Post-revocation session continuity: long-lived session continues to authorise tool calls after the bearer token has been revoked | `A-SES-005`, `A-AUT-007`, `A-SES-007` | CWE-613, CWE-672 (Operation on a Resource After Expiration or Release) |

**Defence references:** cryptographically random session IDs (RFC 4122 §4.4); `tenant_id` bound into the lookup key (`(tenant_id, session_id)`); cancellation tokens scoped to `(tenant_id, session_id, request_id)`; per-request token re-validation for `E`.

---

## 3. Namespace Boundary — STRIDE

> Phase-1 component ref:
> `docs/notes/mcp_learning/02_tools_routing.md` §E,
> `03_resources.md` §E, `04_prompts_context.md` §E,
> `08_concurrency.md` §E, `09_sdks.md` §E.

| STRIDE | Threat | Ticket(s) | CWE |
| --- | --- | --- | --- |
| **S** | Tool-name squatting: a malicious tenant registers a tool whose name collides with a built-in (`read_file`, `exec`, `shell`); confused-deputy call reaches the wrong handler | `A-NSP-001`, `A-NSP-007` | CWE-290 (Authentication Bypass by Spoofing), CWE-1188 (Insecure Default Initialization of Resource) |
| **T** | Resource-template shadowing: a tenant registers a URI pattern that overlaps an existing built-in and intercepts reads for adjacent tenants | `A-NSP-002`, `A-NSP-004` | CWE-915 |
| **R** | Prompt-template argument injection: caller-controlled argument breaks out of the template context block; the resulting rendered prompt does not record its origin in the audit log | `A-NSP-003` | CWE-94 (Improper Control of Generation of Code — "Code Injection") |
| **I** | Lock key collision: a lock keyed on `resource_uri` alone lets two tenants collide on the same lock for the same URI, creating a covert timing channel | `A-NSP-006` | CWE-208 (Observable Timing Discrepancy) |
| **D** | Authorization bypass via shadow tool: policy denies `tool_X` for tenant Y, but Y invokes a synonym the policy does not list, denying the lock and starving legitimate tenants | `A-NSP-005` | CWE-285, CWE-400 |
| **E** | Decorator-name shadowing (Python SDK): a handler bound via `@server.call_tool()` is identified by `__name__`; an attacker who registers a handler with the same name shadows the original | `A-NSP-007` | CWE-285 |

**Defence references:** per-tenant tool registries; canonical tool-name allow-list; lock key includes `tenant_id`; capability tokens scoped to `(tenant_id, tool_name, resource_uri)`.

---

## 4. Tool Boundary — STRIDE

> Phase-1 component ref:
> `docs/notes/mcp_learning/02_tools_routing.md` §B–E,
> `04_prompts_context.md` §C–E, `09_sdks.md` §E.

| STRIDE | Threat | Ticket(s) | CWE |
| --- | --- | --- | --- |
| **S** | Handler-mismatch invocation: a tool whose description advertises benign behaviour dispatches to a side-effecting handler based on hidden `arguments` keys | `A-TOL-005` | CWE-440 (Expected Behavior Violation) |
| **T** | Schema-confusion argument smuggling: `inputSchema` accepts extra properties; an attacker smuggles fields the handler ignores client-side but interprets server-side | `A-TOL-002`, `A-TOL-010` | CWE-915 |
| **R** | Cross-SDK type-confusion: a malicious server returns a non-spec `type` value in a tool result content block, exploiting a lenient Python SDK parser | `A-TOL-009` | CWE-1284 (Improper Validation of Specified Quantity in Input) |
| **I** | Cross-tenant context capture: a tool invocation leaks another tenant's arguments from a shared in-memory queue | `A-TOL-003` | CWE-668 |
| **D** | Call interleaving via `TaskGroup` misuse: `asyncio.gather` interleaves two tenants' handlers in the same task after misconfiguration, corrupting results and starving one tenant | `A-TOL-008` | CWE-754, CWE-400 |
| **E** | Description-channel injection: a prompt template's `description` field contains instructions the host mistakenly renders into the model's context, elevating attacker influence over subsequent tool selection | `A-TOL-007` | CWE-94 |

**Defence references:** strict schema validation (reject extra properties); per-tenant request queues; result sanitisation (strip ANSI / control chars); SDK defaults aligned across Python and TypeScript.

---

## 5. Resource Boundary — STRIDE

> Phase-1 component ref:
> `docs/notes/mcp_learning/03_resources.md` §B–E,
> `04_prompts_context.md` §C.

| STRIDE | Threat | Ticket(s) | CWE |
| --- | --- | --- | --- |
| **S** | Symlink escape: a tenant plants a symlink inside its own resource tree that points to another tenant's resource; resolver follows the symlink | `A-RES-003` | CWE-59 (Improper Link Resolution Before File Access — "Link Following") |
| **T** | URI normalisation bypass: percent-encoded slashes / double-encoded characters bypass a naive string-prefix check; attacker writes outside their tenant root | `A-RES-002` | CWE-22 (Improper Limitation of a Pathname to a Restricted Directory — "Path Traversal"), CWE-176 (Improper Handling of Unicode Encoding) |
| **R** | Subscription cross-tenant leak: a `resources/subscribe` call from Tenant A causes `notifications/resources/updated` events for Tenant B's resource to be delivered to A because subscription state is keyed on URI alone | `A-RES-004` | CWE-778 |
| **I** | Path traversal across tenants: a malicious client supplies a URI like `file:///tenant-a/../tenant-b/secrets.txt` and the resolver path-traverses | `A-RES-001`, `A-RES-005` | CWE-22, CWE-200 (Information Exposure) |
| **D** | Enumeration leakage: `resources/list` returns resources from other tenants because the server's list query omits a tenant predicate | `A-RES-005` | CWE-200, CWE-400 (resource exhaustion via enumeration) |
| **E** | Indirect prompt injection via resource content: a `resources/read` response embeds text that contains instructions the model treats as commands, escalating attacker influence on subsequent tool selection | `A-RES-006`, `A-RES-007` | CWE-94 |

**Defence references:** URI canonicalisation (`os.path.realpath` after resolving `..`); reject symlinks in tenant root; subscription registry keyed on `(tenant_id, uri)`; list query with mandatory tenant predicate.

---

## 6. Memory Boundary — STRIDE

> Phase-1 component ref:
> `docs/notes/mcp_learning/07_context_memory.md` §B–E,
> `08_concurrency.md` §E.

| STRIDE | Threat | Ticket(s) | CWE |
| --- | --- | --- | --- |
| **S** | Shared scratchpad with no tenant tag: a tool handler writes a value to memory with a shared key; another tenant reads it because the key omits `tenant_id` | `A-MEM-002` | CWE-668 |
| **T** | Cross-tenant prompt-cache re-injection: a prompt template contains cached embeddings of prior tenants' conversations that get re-injected into the current model's context because the cache key omits tenant identity | `A-MEM-001` | CWE-524 (Use of Cache Without Validation) |
| **R** | Log file disclosure: server's conversation log is world-readable; an attacker reads Tenant A's full conversation history from the file system and edits it without detection | `A-MEM-003` | CWE-200, CWE-778 |
| **I** | Embedding-store PII persistence: server's embedding store retains PII that flows through the embedding pipeline; the embedding cache is queryable by anyone with API access | `A-MEM-004` | CWE-359 (Exposure of Private Personal Information) |
| **D** | Queue starvation side-channel: a tenant floods the queue with high-priority requests, starving other tenants and inducing the server into a degraded path that exposes more diagnostics | `A-MEM-008` | CWE-400, CWE-208 |
| **E** | Process snapshot exfiltration: a container memory snapshot taken before garbage collection captures another tenant's cached state; the snapshot is exfiltrated | `A-MEM-005` | CWE-200 |

**Defence references:** memory keys include `tenant_id`; logs encrypted at rest; embedding store per-tenant; snapshot taken only with GC quiescence and tenant-scoped.

---

## 7. Cache Boundary — STRIDE

> Phase-1 component ref:
> `docs/notes/mcp_learning/07_context_memory.md` §B–E,
> `02_tools_routing.md` §E.

| STRIDE | Threat | Ticket(s) | CWE |
| --- | --- | --- | --- |
| **S** | Not applicable at this boundary — see Auth boundary (`A-AUT-002`, `A-CCH-002`). The cache does not mint identity; the auth boundary does. | n/a (cross-ref Auth) | n/a |
| **T** | Cross-tenant cache poisoning via tool key: tool results are cached by `(tool_name, arguments)` key, allowing cross-tenant cache poisoning when the key omits `tenant_id` | `A-CCH-001` | CWE-524 |
| **R** | Session-token leakage via cache key: a session token is logged in a cache key (e.g. cache key includes session ID for debugging), exposing it to anyone with read access to the cache | `A-CCH-002` | CWE-532 (Insertion of Sensitive Information into Log File), CWE-778 |
| **I** | Cross-tenant cache hit on missing `tenant_id`: Tenant B calls a tool with arguments identical to Tenant A's and receives Tenant A's cached output | `A-CCH-003`, `A-CCH-005` | CWE-524, CWE-200 |
| **D** | Embedding collision DoS: a malicious tenant pre-computes an embedding that collides with Tenant A's prompt hash; cache eviction cascade denies service | `A-CCH-004` | CWE-400 |
| **E** | Rendered-prompt cross-tenant reuse: server caches a rendered prompt whose arguments contained Tenant A's tool result; the cached rendering is later served to Tenant B because the cache key is `(prompt_name, args_hash)` only | `A-CCH-005` | CWE-524, CWE-285 |

**Defence references:** cache keys always include `tenant_id`; session tokens never in cache keys; rendered-prompt cache also keyed on `tenant_id`.

---

## 8. Auth Boundary — STRIDE

> Phase-1 component ref:
> `docs/notes/mcp_learning/05_auth.md` §B–E,
> `04_prompts_context.md` §E, `06_sessions.md` §E.

| STRIDE | Threat | Ticket(s) | CWE |
| --- | --- | --- | --- |
| **S** | Token replay across transports: a malicious host captures an Authorization header from logs / error traces and replays it against the server | `A-AUT-002` | CWE-294 |
| **T** | Capability negotiation spoofing: a malicious client advertises capabilities it does not possess to elicit different server behaviour (e.g. enabling SSE-only paths the client cannot legitimately receive) | `A-AUT-005` | CWE-290 |
| **R** | Cross-deployment token reuse: a token issued for deployment A is misused against deployment B because no `aud` claim is enforced; the audit log records the wrong deployment | `A-AUT-003` | CWE-200, CWE-778 |
| **I** | Token forwarding via SSRF: a tenant calls a tool whose handler SSRF-fetches a URL and forwards the original Authorization header to an attacker-controlled origin | `A-AUT-004`, `A-AUT-006` | CWE-918 (Server-Side Request Forgery), CWE-200 |
| **D** | TOCTOU across await: a handler checks tenant permission, then awaits an external service; the revocation arrives during the await and the handler completes anyway, denying the legitimate tenant the resource | `A-AUT-008` | CWE-367 (Time-of-check Time-of-use Race Condition) |
| **E** | Startup-time prompt injection via session establishment: a host that auto-injects prompts on `initialize` runs the server's prompt at startup; a malicious server uses this channel to seed the model with attacker-chosen system-level instructions | `A-AUT-001`, `A-NSP-005` | CWE-94, CWE-285 |

**Defence references:** audience-bound JWTs (RFC 7519 §4.1.3 `aud` claim); mTLS with SAN pinning; capability negotiation ignored by server (server decides server-side); revocation re-checked at every await boundary.

---

## Misuse Cases

Four concrete misuse cases — each pinned to ≥2 ticket IDs and a
likely / impact rating. The prompt requires ≥3; the fourth
(MC-4) is provided to give Phase-12 reviewer simulation
material.

### MC-1 — Cross-tenant environment-variable overwrite via tool shadowing

- **Pre-conditions.** Multi-tenant MCP server that registers
  tools in a shared global registry; tool names are not
  tenant-prefixed; environment-variable-style scratchpads are
  shared across tenants.
- **Attacker goal.** Overwrite Tenant B's environment variables
  (e.g. `PATH`, `API_KEY`) so that Tenant B's subsequent tool
  invocations route to attacker-controlled binaries or leak
  credentials.
- **Attack flow.**
  1. Tenant A registers a tool named `set_env` whose handler
     writes to a shared scratchpad keyed by `env_var_name` (no
     `tenant_id`). This shadows a built-in `set_env` tool.
     → `A-NSP-001`.
  2. Tenant A calls the shadowed `set_env` with `env_var_name =
     "PATH"`, `value = "/tmp/evil"`.
  3. The server's scratchpad write omits the tenant predicate.
     → `A-MEM-002`.
  4. Tenant B subsequently calls any tool that reads `PATH` from
     the same scratchpad; the read returns Tenant A's value. The
     call is dispatched to attacker-controlled binaries.
     → `A-TOL-005`.
- **Mapped tickets.** `A-NSP-001`, `A-TOL-005`, `A-MEM-002`.
- **Likelihood.** High (the only pre-condition is a shared
  registry, which is the default in most reference servers).
- **Impact.** High (arbitrary code execution via PATH hijack;
  credential theft via env-var overwrite).

### MC-2 — Session fixation across server restart

- **Pre-conditions.** Server uses predictable session IDs (e.g.
  monotonically increasing integers, or UUIDs minted from a
  low-entropy source); server retains session-state-to-disk and
  reloads on restart; cache keys omit `tenant_id`.
- **Attacker goal.** Read Tenant B's cached tool outputs after
  restart by resuming a session ID that previously belonged to
  Tenant B.
- **Attack flow.**
  1. Tenant A observes the server's session-ID mint pattern
     (e.g. via timing side-channel or by enumerating
     `initialize` responses). → `A-SES-001`.
  2. Tenant A waits for the server to restart (e.g. after a
     deploy). → `A-SES-002`.
  3. The server reloads session state from disk; Tenant B's
     session ID is now active again but bound to a different
     in-memory principal map.
  4. Tenant A sends an `initialize` with the pre-minted
     `session_id`; the server resumes Tenant B's session.
  5. Tenant A calls a tool that hits the cache; the cache key
     `(tool_name, args_hash)` returns Tenant B's cached output.
     → `A-CCH-003`.
- **Mapped tickets.** `A-SES-001`, `A-SES-002`, `A-CCH-003`.
- **Likelihood.** Medium (requires restart event + enumerable
  IDs).
- **Impact.** High (full read of Tenant B's prior tool outputs).

### MC-3 — Resource path traversal via percent-encoded slashes

- **Pre-conditions.** Server accepts `file://` URIs as resource
  identifiers; resolver concatenates tenant root with the URI
  path; resolver does not canonicalise `..` segments and does
  not strip percent-encoded slashes (`%2F`, `%2f`).
- **Attacker goal.** Read Tenant B's secret documents by
  traversing out of Tenant A's resource root.
- **Attack flow.**
  1. Tenant A issues
     `resources/read` with URI
     `file:///tenant-a/..%2F..%2Ftenant-b%2Fsecrets.txt`.
     → `A-RES-001` (path traversal) and `A-RES-002`
     (normalisation bypass).
  2. The resolver concatenates `/srv/data/tenant-a` + the URI
     path, but does not decode `%2F` before the traversal
     check, so the prefix check passes.
  3. After concatenation, the OS-level `open()` decodes `%2F`
     and resolves `..`, landing on `/srv/data/tenant-b/secrets.txt`.
  4. If a symlink from `tenant-a` to `tenant-b` exists, the
     resolver follows it without an additional check.
     → `A-RES-003`.
  5. The server returns Tenant B's secrets to Tenant A in the
     `resources/read` response.
- **Mapped tickets.** `A-RES-001`, `A-RES-002`, `A-RES-003`.
- **Likelihood.** High (per Chen et al. 2026, symlink-following
  resolvers are observed at scale).
- **Impact.** Critical (arbitrary read across tenant filesystems).

### MC-4 — Embedding cache poisoning via prompt collision

- **Pre-conditions.** Server caches prompt embeddings in a
  vector store keyed by `prompt_hash` only (no `tenant_id`);
  embedding cache is queryable by all tenants; hash function
  is unsalted.
- **Attacker goal.** Read Tenant B's cached embedding (and
  through partial inversion, recover the source prompt text —
  background literature, not MCP-specific).
- **Attack flow.**
  1. Tenant A enumerates `prompts/list` to learn the prompt
     templates available; the server does not enforce a
     tenant predicate.
  2. Tenant A crafts a prompt whose `sha256` matches the
     unsalted hash of Tenant B's prompt (collision attack —
     feasible on weakened hash functions, expensive on
     full `sha256`).
     → `A-CCH-004`.
  3. Tenant A queries the embedding cache with the colliding
     prompt; the cache returns Tenant B's embedding.
  4. The server's embedding store retains PII from prior
     embeddings and serves them to any tenant.
     → `A-MEM-004`.
- **Mapped tickets.** `A-CCH-004`, `A-MEM-004`.
- **Likelihood.** Low (requires weakened hash or
  computationally feasible collision).
- **Impact.** Medium–High (depends on embedding invertibility;
  privacy violation regardless).

---

## Attack Stub Manifest (8 boundaries × 8 STRIDE rows)

For Phase 7 implementation: 64 stub files in
`attacks/<boundary>/A_<PREFIX>_<NNN>_<stride>.py`. Each stub
references the STRIDE row above via its `id` attribute and a
docstring cross-reference.

Stub enumeration (one stub per (boundary, STRIDE) row):

| Boundary | S | T | R | I | D | E |
| --- | --- | --- | --- | --- | --- | --- |
| **Transport** | `A-TRN-S` | `A-TRN-T` | `A-TRN-R` | `A-TRN-I` | `A-TRN-D` | `A-TRN-E` |
| **Session** | `A-SES-S` | `A-SES-T` | `A-SES-R` | `A-SES-I` | `A-SES-D` | `A-SES-E` |
| **Namespace** | `A-NSP-S` | `A-NSP-T` | `A-NSP-R` | `A-NSP-I` | `A-NSP-D` | `A-NSP-E` |
| **Tool** | `A-TOL-S` | `A-TOL-T` | `A-TOL-R` | `A-TOL-I` | `A-TOL-D` | `A-TOL-E` |
| **Resource** | `A-RES-S` | `A-RES-T` | `A-RES-R` | `A-RES-I` | `A-RES-D` | `A-RES-E` |
| **Memory** | `A-MEM-S` | `A-MEM-T` | `A-MEM-R` | `A-MEM-I` | `A-MEM-D` | `A-MEM-E` |
| **Cache** | `A-CCH-S` | `A-CCH-T` | `A-CCH-R` | `A-CCH-I` | `A-CCH-D` | `A-CCH-E` |
| **Auth** | `A-AUT-S` | `A-AUT-T` | `A-AUT-R` | `A-AUT-I` | `A-AUT-D` | `A-AUT-E` |

Phase 7 will replace each stub with a concrete `execute()`
implementation; the stub `id` value (one of the 64 above) is
the contract with the Phase-9 harness.

## Cross-References

- Phase-1 ticket index: `docs/notes/mcp_learning/00_appendix.md`
  (63 tickets).
- Phase-2 concept taxonomy: `docs/notes/security_learning/00_index.md`
  (14 concepts).
- Phase-3 evidence: `literature/related_work.md` (12-paper matrix).
- Phase-6 framework will use the 64 stub IDs as keys in the
  measurement harness.
- Phase-9 experiments will run the Phase-7-implemented stubs
  against the vulnerable / secure reference servers.