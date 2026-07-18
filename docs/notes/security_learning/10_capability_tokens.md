# 10 — Capability Tokens

> Phase 2, Concept 10 of 14. Per `prompts/02_security_learning.md` A–F
> rubric. Concept coverage: **Architecture** macro-category.

## (A) Formal Definition

**Capability tokens** are concrete, on-the-wire embodiments of
capabilities (Concept 09). They are signed, structured data
carrying a description of the access rights granted to a holder.
The dominant standards family is:

- **OAuth 2.0** — **RFC 6749 "The OAuth 2.0 Authorization
  Framework"** (Hardt, Ed., 2012); **RFC 6750 "The OAuth 2.0
  Authorization Framework: Bearer Token Usage"** (Jones, Hardt,
  2012).
- **JWT** — **RFC 7519 "JSON Web Token (JWT)"** (Jones, Bradley,
  Sakimura, 2015); tokens are signed (JWS, RFC 7515) and optionally
  encrypted (JWE, RFC 7516).
- **Macaroons** — Birgisson et al., "Macaroons: Cookies with
  Contextual Caveats for Decentralized Authorization in the Cloud"
  (NDSS 2014).
- **PASETO** — "Platform-Agnostic Security Tokens" (proprietary
  successor design; specific revision requires empirical
  verification).

The defining property: a capability token is *opaque to the
holder* (the holder cannot forge or amplify) but *verifiable by
the issuer* (the issuer's signature proves the rights).

## (B) Threat Model

- **Attacker position.** A token holder who attempts to replay,
  redirect, or amplify the token beyond its intended audience,
  expiry, or scope.
- **Assets.** The objects whose access is mediated by the token.
- **Preconditions.** (i) Tokens lack audience (`aud`) claims. (ii)
  Tokens lack expiry (`exp`) or the server does not enforce it.
  (iii) Tokens lack scope and the server has no per-scope policy.

## (C) Real-World / Theoretical Example

An MCP deployment issues a JWT with claims
`{sub: tenant_A, scope: tools:read}`. The token is used to call
the `delete_record` tool — a scope the token does not carry. The
server, lacking a scope-policy check, accepts the call. Tenant A
deletes Tenant B's record. This is the failure mode capability
tokens are designed to prevent.

## (D) Standard Defenses

- **Audience claim.** Tokens carry an `aud` claim; the server
  rejects tokens whose `aud` does not match the server's identity.
- **Expiry claim.** Tokens carry `exp`; the server rejects expired
  tokens.
- **Not-before claim.** Tokens carry `nbf`; the server rejects
  tokens used before their intended time.
- **Scope / permissions claim.** Tokens carry the scopes the holder
  is authorised to use; the server enforces per-method policies
  against scopes.
- **Token rotation.** Short-lived tokens; refresh-token rotation
  with reuse detection.
- **Audience-scoped signing keys.** Per-deployment signing keys so
  that a token issued for deployment A cannot be verified by
  deployment B.

## (E) Open Research Problems

- **Token side-channels.** Even with all standard claims enforced,
  tokens leak information through timing of validation, error
  messages, and logging.
- **Cascading revocation.** A user's revocation at the identity
  provider must propagate to all tokens issued under the user's
  authority; current implementations are inconsistent.
- **Cross-protocol token portability.** MCP deployments that bridge
  to OAuth 2.0, OIDC, SAML, and Kerberos have inconsistent token
  semantics; a unified capability model is not yet standardised.

## (F) Direct Relation to MCP Architecture

- **MCP boundary.** `auth`.
- **MCP primitive.** `initialize` (token exchange); every
  authenticated method (per-request token verification).
- **Phase-1 ticket cross-references.**
  - `A-AUT-002` — token replay across transports.
  - `A-AUT-003` — cross-deployment token reuse (no audience claim).
  - `A-AUT-007` — post-revocation session continuity.
- **Source.** `docs/notes/mcp_learning/05_auth.md` §B–E.