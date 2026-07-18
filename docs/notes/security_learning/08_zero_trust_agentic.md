# 08 — Zero Trust in Agentic Systems

> Concept 8 of 14.
> rubric. Concept coverage: **Architecture** macro-category.

## (A) Formal Definition

**Zero Trust** is a security architecture that rejects the
traditional perimeter model ("inside the firewall = trusted") in
favour of *continuous, per-request verification* of identity,
device posture, and authorisation. The canonical reference is **NIST
Special Publication 800-207 "Zero Trust Architecture"** (Rose,
Borcherding, Mitchell, Connelly, 2020). The core tenets are:

- No implicit trust based on network location.
- All access requests are authenticated, authorised, and logged.
- Access is granted at the smallest possible scope (least privilege).
- Policy is enforced as close to the protected resource as possible.
- The enterprise monitors and verifies the integrity and security
  posture of all assets.

In *agentic systems* (MCP servers, LLM tool-using agents,
multi-agent orchestration), Zero Trust extends to: (i) treating
*every* tool call as if it came from an untrusted caller; (ii)
treating *every* tool result as if it were attacker-controlled
data; (iii) re-verifying principal identity on every request
rather than relying on session state.

## (B) Threat Model

- **Attacker position.** Anyone in the trust graph: a malicious
  tenant, a compromised agent, a malicious tool result, a network
  adversary between hops.
- **Assets.** All tenant data and capabilities reachable via the
  agent.
- **Preconditions.** The system has any actor or content source that
  is treated as "trusted by default" — an internal subnet, a
  server-local file, a cached tool result.

## (C) Real-World / Theoretical Example

A traditional MCP deployment treats all `localhost` connections as
trusted and only enforces authentication on remote transports. An
attacker who achieves code execution on the same host (via a
separate vulnerability) connects to the MCP server's `stdio` or
local SSE port and bypasses all authentication. A Zero Trust
deployment would require an authenticated token on every transport
regardless of network location.

## (D) Standard Defenses

- **Per-request authentication.** The server re-validates the token
  on every request.
- **Tool-result sanitisation.** Treat all tool output as untrusted
  input; run it through a sanitiser before further model use.
- **Least-privilege tokens.** Issue narrowly-scoped tokens per
  tenant, per session, per tool category.
- **Continuous monitoring.** Log and audit every request; alert on
  deviation from baseline.
- **mTLS everywhere.** Mutual TLS on every transport, including
  localhost (where applicable).

## (E) Open Research Problems

- **Cost of verification.** Re-authenticating every request
  increases latency and operational cost; balancing the cost of
  verification against the residual risk is poorly characterised.
- **Trust propagation in multi-agent graphs.** When Agent A calls
  Tool X which calls Tool Y, the trust context may be lost or
  inflated along the chain.
- **Zero Trust for embeddings and caches.** Pre-computed embeddings
  and cached tool outputs violate Zero Trust's "verify every
  request" principle unless their provenance is audited.

## (F) Direct Relation to MCP Architecture

- **MCP boundary.** *All eight boundaries.* Zero Trust is an
  architectural principle that applies to every layer.
- **MCP primitive.** Every JSON-RPC request; every tool result;
  every resource payload.
- **Phase-1 ticket cross-reference.** Zero Trust is the
  *correctness goal* against which every Phase-1 ticket represents
  a partial failure. The 63 Phase-1 tickets are an empirical
  catalogue of where current MCP deployments violate Zero Trust
  principles.
- **Source.** All nine Phase-1 component files; conceptual
  grounding in NIST SP 800-207.