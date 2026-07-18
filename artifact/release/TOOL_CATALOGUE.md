# MCP Server Tool Catalogue

The reference `mcp_servers/vulnerable/` and `mcp_servers/secure/`
implementations expose the following tool catalogue. The
*vulnerable* server exposes every tool to every tenant; the
*secure* server filters by tenant via the per-tenant tool
registry.

| Tool name     | Arguments                            | Vulnerable | Secure (both tenants) |
|---------------|--------------------------------------|:----------:|:---------------------:|
| `echo`        | `{text: string}`                     | ✓          | ✓                     |
| `get_secret`  | `{key: string}`                      | ✓          | ✓                     |
| `list_tenants`| `{}`                                 | ✓          | ✗ (admin-only)        |
| `set_env`     | `{name: string, value: string}`      | ✓          | ✓                     |
| `read_file`   | `{uri: string}` (file:// scheme)     | ✓          | ✓ (canonicalised)     |
| `write_file`  | `{uri: string, content: string}`     | ✓          | ✓ (canonicalised)     |
| `cache_get`   | `{key: string}`                      | ✓          | ✓ (tenant-prefixed)   |
| `cache_put`   | `{key: string, value: any}`          | ✓          | ✓ (tenant-prefixed)   |

Tool-handler implementations are in
`mcp_servers/<vulnerable|secure>/handlers/`. The schema for each
tool (input/output) is in the tool's
`inputSchema` attribute; the secure server validates every input
against the schema with `extra="forbid"`.

## How the secure server's defense middleware maps to tools

- **Per-tenant tool registry (namespace).** Each tool's
  `execute()` is wrapped with a registry check:
  `if tool_name not in REGISTRY[tenant_id]: raise Forbidden`.
- **Tenant-prefixed cache keys (cache).** `cache_get` /
  `cache_put` prepend `tenant_id` to the user-supplied key.
- **Resource-path canonicalisation (resource).** `read_file` /
  `write_file` apply `os.path.realpath` after percent-decoding
  before any tenant-prefix check.
- **Audience-bound JWTs (auth).** Every `execute()` call
  re-validates the bearer token's `aud` claim against the
  resolved `tenant_id` at the await boundary.