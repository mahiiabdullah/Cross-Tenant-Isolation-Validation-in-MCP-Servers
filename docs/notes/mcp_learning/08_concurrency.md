# 08 — Multi-Client to Single-Server Concurrency

> Phase 1, Component 8 of 9. Every (E) bullet references a forward ticket ID
> of the form `A-{boundary}-{nnn}`; Phase 5 will resolve these IDs in
> `docs/04_Attack_Taxonomy.md`.

## (A) Purpose

A single MCP server typically serves **many concurrent clients** — multiple
tenants, multiple agents per tenant, and multiple parallel requests per
agent. Concurrency primitives (locks, queues, worker pools, async tasks,
thread pools) determine whether shared mutable state is correctly
partitioned across these clients. Concurrency bugs are a frequent root
cause of cross-tenant leakage: a contextvar captured in the wrong task, a
lock held across tenants, or a queue that mixes messages from multiple
principals.

## (B) Internal Workflow

Common concurrency patterns in reference MCP servers:

| Pattern | Shape | Tenant-isolation property |
|---|---|---|
| asyncio + contextvars | Per-task `ContextVar` carries `tenant_id` | Strong only if no `asyncio.gather` interleaves tasks without preserving context |
| Thread pool | Per-thread local storage | Strong only if the worker is bound to the request that scheduled it |
| Process pool | OS-level isolation | Strong unless IPC channel leaks context |
| Shared queue | Single FIFO across all clients | Insecure by default; tenant must be tagged at enqueue and dequeue |
| Lock per resource | `Lock` keyed on resource URI | Strong only if the key includes `tenant_id` |
| Global lock | One `Lock` for the server | Serialises everything; correctness possible but performance collapses; tenant correctness requires careful context propagation |

Scheduling is implementation-defined. Some servers implement
**fair-queueing** to avoid head-of-line blocking; others use
**priority queues** that can be abused by a tenant who floods the queue
with high-priority requests.

## (C) Data Flow

A typical asyncio request handler:

```
[request arrives on transport]
    │
    ▼  (transport reader pushes onto inbound queue)
[server.dispatch()]
    │
    ├──► authenticate(token) -> principal
    ├──► bind principal to current_task via ContextVar
    ├──► handler = tool_registry[params.name]
    └──► result = await handler(**params.arguments)
            │
            ▼  (handler may await other tools; context must propagate)
        [result]
            │
            ▼  (sanitise, log, cache)
        [response]
```

The `await` points are the **context-propagation hazards**: every `await`
boundary is an opportunity for the asyncio scheduler to switch tasks. If
the binding `principal -> current_task` is lost at an `await`, the next
task may run with the wrong principal.

A shared queue data flow (vulnerable by default):

```
Tenant A enqueues:  {"tenant": "A", "msg": {...}}
Tenant B enqueues:  {"tenant": "B", "msg": {...}}
        │
        ▼  (server dequeues without checking "tenant" tag)
[handler runs with whichever message is on top]
```

## (D) Inherent Security Implications

- **ContextVar loss across `await`.** A handler that does
  `principal = principal_var.get()` and then awaits without re-binding
  can pick up a different tenant's principal in the resumed task.
- **Race conditions on shared state.** If a tool updates a shared
  structure (rate-limit counter, cache, audit log) without proper
  locking, the update may apply to the wrong tenant.
- **Worker pool reuse.** A worker that retained state from a previous
  request (residual locals, thread-locals) leaks prior-tenant data.
- **Cancellation propagation.** Cancelling one tenant's task may
  inadvertently cancel another's if cancellation tokens are not
  scoped.
- **Starvation / DoS.** A tenant that floods the queue can starve
  others; cross-tenant DoS is a confidentiality-adjacent concern (the
  starved tenant's data may become observable to a co-located tenant
  in some degraded paths).
- **Time-of-check / time-of-use.** A pattern that checks tenant
  permission at queue-dequeue and then executes later may execute
  after the tenant has been revoked.

## (E) Theoretical Attack Surface

- **E-1.** A handler binds `principal` to a ContextVar but loses it at
  an `await`, so a subsequent tool call runs with **Tenant B's
  principal** while still using Tenant A's session resources. →
  `A-SES-007` (session: ContextVar loss across await; cross-referenced
  from concurrency).
- **E-2.** A shared queue dispatches a message **without checking the
  embedded tenant tag**, and the handler runs with the queue-top
  message's payload under the dequeued principal. →
  `A-MEM-006` (memory: shared queue dequeue without tenant check;
  cross-referenced from concurrency).
- **E-3.** A worker pool retains **thread-local state** across
  requests, so the next request sees the previous tenant's scratchpad.
  → `A-MEM-007` (memory: thread-local residual).
- **E-4.** A lock keyed on `resource_uri` alone allows two tenants to
  **collide on the same lock** for the same URI, creating a covert
  timing channel. → `A-NSP-006` (namespace: lock key collision;
  cross-referenced).
- **E-5.** A tenant **floods the queue** with high-priority requests,
  starving other tenants and inducing the server into a degraded path
  that exposes more diagnostics. → `A-MEM-008` (memory: queue
  starvation side-channel).
- **E-6.** A handler checks tenant permission, then awaits an external
  service; the **revocation** arrives during the await and the
  handler completes anyway. → `A-AUT-008` (auth: TOCTOU across
  await; cross-referenced).
- **E-7.** A `asyncio.gather` interleaves two tenants' handlers in the
  same task after a misconfigured `TaskGroup`, causing **call
  interleaving** (Tenant A's call to `tool_X` followed by Tenant B's
  call to `tool_X` in the same task). → `A-TOL-008` (tool: call
  interleaving via TaskGroup misuse; cross-referenced).

All ticket IDs reference forward entries in
`docs/04_Attack_Taxonomy.md` and will be materialised by Phase 5.