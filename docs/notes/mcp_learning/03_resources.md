# 03 — Resources & Resource Templates

> Phase 1, Component 3 of 9. Every (E) bullet references a forward ticket ID
> of the form `A-{boundary}-{nnn}`; Phase 5 will resolve these IDs in
> `docs/04_Attack_Taxonomy.md`.

## (A) Purpose

A **Resource** in MCP is a server-managed, addressable artifact —
typically a file, blob, or URI-identified record — that a client can read,
subscribe to, or enumerate. Resource **templates** are URI patterns with
parameters, allowing a client to materialise a concrete resource URI at
runtime. The resource layer is the file-system / object-store analogue of
the tool layer and is the second most consequential capability surface for
cross-tenant leakage.

## (B) Internal Workflow

Primary methods:

- `resources/list` — enumerate concrete resources visible to the calling
  client.
- `resources/templates/list` — enumerate URI templates.
- `resources/read` — fetch the bytes of a specific resource URI.
- `resources/subscribe` — register interest in change notifications for
  a URI (spec section requires empirical verification).
- `notifications/resources/updated` — server-pushed notification that a
  subscribed resource changed.
- `notifications/resources/list_changed` — server-pushed notification
  that the resource catalog changed.

A typical URI scheme for resources is opaque to the protocol but commonly
takes the form `<scheme>://<path>` (e.g. `file:///tenant-a/docs/x.md`,
`postgres://app/tables/users`); concrete schemes are server-defined.

## (C) Data Flow

`resources/read` request:

```json
{
  "jsonrpc": "2.0",
  "id": 11,
  "method": "resources/read",
  "params": {"uri": "file:///tenant-a/docs/x.md"}
}
```

`resources/read` response (text blob):

```json
{
  "jsonrpc": "2.0",
  "id": 11,
  "result": {
    "contents": [
      {
        "uri": "file:///tenant-a/docs/x.md",
        "mimeType": "text/markdown",
        "text": "# Heading\n..."
      }
    ]
  }
}
```

`resources/read` response (binary blob):

```json
{
  "jsonrpc": "2.0",
  "id": 11,
  "result": {
    "contents": [
      {
        "uri": "file:///tenant-a/docs/x.pdf",
        "mimeType": "application/pdf",
        "blob": "<base64-encoded bytes>"
      }
    ]
  }
}
```

`resources/subscribe` request:

```json
{
  "jsonrpc": "2.0",
  "id": 12,
  "method": "resources/subscribe",
  "params": {"uri": "file:///tenant-a/docs/x.md"}
}
```

Resource URI template:

```json
{
  "uriTemplate": "file:///tenants/{tenant_id}/docs/{doc_id}.md",
  "name": "Tenant Document",
  "description": "Markdown docs within a tenant's directory.",
  "mimeType": "text/markdown"
}
```

## (D) Inherent Security Implications

- **URI is the only access-control handle.** The server receives a URI
  string and must enforce tenant scoping on it; there is no protocol-level
  per-resource ACL.
- **Path traversal.** A naive resolver that concatenates tenant root with
  a URI path (`..%2F..%2Ftenant-b/...`) escapes the tenant's scope. URL-
  decoding/normalisation timing differences introduce TOCTOU.
- **Symlink following.** If the server follows symlinks, a tenant can
  point at another tenant's data.
- **No tenant scoping in URI scheme.** URI syntax does not embed a
  required `tenant_id`; the server must enforce scoping itself.
- **Subscription fan-out.** `resources/subscribe` notifies on changes;
  if subscription state is shared across tenants, notifications can
  leak resource existence to the wrong tenant.
- **Pagination / listing leakage.** `resources/list` may return more
  than the requesting tenant should see if the server filters only on
  the requester's identity but caches across sessions.
- **Template parameter trust.** A malicious client can request a
  template URI with values designed to escape the pattern (`{tenant_id}
  = "../other-tenant"`).

## (E) Theoretical Attack Surface

- **E-1.** A malicious client supplies a URI like
  `file:///tenant-a/../tenant-b/secrets.txt` and the resolver
  **path-traverses** to another tenant. →
  `A-RES-001` (resource: path traversal across tenants).
- **E-2.** A malicious client supplies a URI containing **percent-encoded
  slashes** (`%2F`) or **double-encoded** characters to bypass a naive
  string-prefix check. → `A-RES-002` (resource: URI normalisation bypass).
- **E-3.** A tenant plants a **symlink** inside its own resource tree
  that points to another tenant's resource; the resolver follows the
  symlink. → `A-RES-003` (resource: symlink escape).
- **E-4.** A `resources/subscribe` call from Tenant A causes
  `notifications/resources/updated` events for **Tenant B's** resource
  to be delivered to A because the subscription registry is keyed on
  URI alone. → `A-RES-004` (resource: subscription cross-tenant leak).
- **E-5.** A `resources/list` response **includes resources from other
  tenants** because the server's list query omits a tenant predicate.
  → `A-RES-005` (resource: enumeration leakage).
- **E-6.** A tenant registers a URI template whose pattern overlaps an
  existing built-in (`file:///{tenant}/...`) and **intercepts** reads
  for adjacent tenants. → `A-NSP-002` (namespace: resource-template
  shadowing; cross-referenced from resources).
- **E-7.** A `resources/read` response embeds **content** (text or
  blob) that contains instructions the model treats as commands.
  → `A-RES-006` (resource: indirect prompt injection via content).

All ticket IDs reference forward entries in
`docs/04_Attack_Taxonomy.md` and will be materialised by Phase 5.
