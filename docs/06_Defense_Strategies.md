# 06 — Defense Strategies

> TBD: enumerate defenses per boundary, with cost and effectiveness notes.

## Candidates

| Defense | Boundary | Mechanism | Cost |
| --- | --- | --- | --- |
| Per-tenant tool registry | Namespace | Static allowlist of tools per tenant | Low |
| Session token binding | Session | Cryptographic binding of session id to tenant token | Low |
| Resource path canonicalization | Resource | Reject URIs that escape tenant root | Low |
| Prompt-content scanning | Prompt | Filter known injection patterns from tool results | Medium |
| Cache key namespacing | Cache | Tenant-prefixed cache keys | Low |
| Memory per-tenant sharding | Memory | Separate memory stores keyed by tenant | Medium |
| Scope-minimized auth tokens | Auth | Issue narrow OAuth-like scopes per tenant | Medium |
| Mutual TLS / channel auth | Transport | Strong transport-layer identity | Medium |

Each defense is implemented in `mcp_servers/secure/` and registered via a uniform middleware interface (TBD).