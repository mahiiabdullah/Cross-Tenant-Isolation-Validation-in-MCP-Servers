# 00 — Security Concepts Taxonomy Index

> Consolidated index for **Phase 2** of the MCP Isolation Research program.
> Aggregates the 14 concept files in `docs/notes/security_learning/` into a
> single navigable reference. Concept files are individually maintained and
> authoritative; this file is regenerated from them.
>
> Per `prompts/00_master.md` and `prompts/02_security_learning.md`, every
> concept file uses the A–F rubric. Every concept's (F) names an MCP
> boundary and references at least one Phase-1 ticket ID from
> `docs/notes/mcp_learning/`.

## Macro-Category Map

| Macro | Concepts | File |
|---|---|---|
| **Injection** (3) | Direct prompt injection · Indirect prompt injection · Tool injection | `01_…md`, `02_…md`, `03_…md` |
| **Isolation** (4) | Multi-tenant isolation · Namespace isolation · Resource/memory isolation · Session isolation | `04_…md`, `05_…md`, `06_…md`, `07_…md` |
| **Architecture** (4) | Zero Trust (agentic) · Capability-based security · Capability tokens · Sandboxing | `08_…md`, `09_…md`, `10_…md`, `11_…md` |
| **Logic** (3) | Context poisoning · Tool confusion · Confused deputy | `12_…md`, `13_…md`, `14_…md` |

> Note: `prompts/02_security_learning.md` states 13 concepts in its
> Done-When gate but lists 14 in its coverage list. This index covers
> all 14 explicit items in the coverage list.

## Concept → MCP Boundary → Primary Source Index

| # | Concept | MCP boundary | Primary source (citation in file) | Phase-1 ticket anchors |
|---|---|---|---|---|
| 01 | Direct prompt injection | tool, auth | OWASP LLM01:2025; MITRE ATLAS AML.T0051 (requires verification) | `A-AUT-001` |
| 02 | Indirect prompt injection | tool, resource, memory | OWASP LLM01:2025 | `A-TOL-001`, `A-RES-006`, `A-MEM-001` |
| 03 | Tool injection | namespace, auth | OWASP LLM05:2025; OWASP LLM07:2025 (legacy) | `A-NSP-001`, `A-NSP-007` |
| 04 | Multi-tenant isolation | (all 8) | CWE-668; CWE-1228; NIST SP 500-299 | (all tickets) |
| 05 | Namespace isolation | namespace | CWE-706; CWE-1007; CWE-22 | `A-NSP-001`–`A-NSP-007` |
| 06 | Resource / memory isolation | resource, memory, cache | CWE-552; CWE-538; CWE-922; CWE-200 | `A-RES-001`–`A-RES-007`; `A-MEM-002`–`A-MEM-008`; `A-CCH-001`–`A-CCH-005` |
| 07 | Session isolation | session, auth | CWE-613; CWE-384; CWE-488; CWE-330 | `A-SES-001`–`A-SES-009`; `A-AUT-007` |
| 08 | Zero Trust (agentic) | (all 8) | NIST SP 800-207 | (architectural — all tickets) |
| 09 | Capability-based security | auth, namespace | Dennis & Van Horn (1966); Levy (1984); Capsicum (FreeBSD 9.0, 2012) | `A-AUT-005`, `A-NSP-005` |
| 10 | Capability tokens | auth | RFC 6749; RFC 6750; RFC 7519; RFC 7515; RFC 7516; Birgisson et al. NDSS 2014 | `A-AUT-002`, `A-AUT-003`, `A-AUT-007` |
| 11 | Sandboxing (WASM/gVisor/Firecracker/OS) | transport, session | W3C WebAssembly Core; WASI Preview 2; gVisor (Lacasse 2018, requires verification); Firecracker (Agache et al. NSDI 2020) | `A-TRN-005`, `A-SES-002` |
| 12 | Context poisoning | memory, cache, tool | CWE-501; CWE-915; Biggio et al. (2012, requires verification) | `A-MEM-001`, `A-MEM-002`, `A-CCH-001`, `A-CCH-005` |
| 13 | Tool confusion | namespace, tool | CWE-441; CWE-1007; CWE-1284 | `A-NSP-001`, `A-TOL-005` |
| 14 | Confused deputy | auth, tool, resource | Hardy (1988); CWE-441; CWE-269; CWE-732 | `A-TOL-005`, `A-AUT-005`, `A-RES-001` |

## Concept Dependency Graph (high level)

```
Injection ──────► Isolation (resource/memory isolation is the
                     containment strategy for indirect injection)
   │
   └──► Logic (tool confusion / confused deputy are the
              routing-level realisation of injection)

Architecture ──► Isolation (capabilities are the *mechanism* by
                 which isolation is enforced; sandboxing is the
                 *substrate*)

Logic ─────────► Architecture (confused-deputy defenses rely on
                 capability attenuation; context-poisoning defenses
                 rely on tenant-prefixed cache keys)
```

## Verifiable vs Requires-Verification Status

| Citation kind | Count | Examples |
|---|---|---|
| Verifiable from training | RFCs, OWASP, NIST, CWE, W3C, classic papers | RFC 6749, RFC 7455, NIST SP 800-207, CWE-441 |
| Requires empirical verification | ATLAS technique IDs, specific paper revisions, OWASP LLM Top-10 revision-specific items | MITRE ATLAS AML.T0051; gVisor paper bib; OWASP LLM Top-10 specific LLM-NN:YYYY IDs |

Every concept file carries explicit *"requires verification"* markers
where applicable, per the prompt's no-hallucination directive.

## Cross-Phase Outputs

- Phase 3 will consume the (A) citations of all 14 files to populate
  `literature/related_work.md`.
- Phase 5 will resolve the Phase-1 ticket IDs listed in (F) into
  STRIDE rows in `docs/04_Attack_Taxonomy.md`.
- Phase 7 will reuse the (D) Standard Defenses and (E) Open Research
  Problems sections when justifying CVSS scores for each attack.
- Phase 11 will use this index as a paper appendix and render the
  accompanying `docs/diagrams/security_taxonomy.dot` to SVG for a
  paper figure.

## Source-of-Truth Files

| File | Macro | # |
|---|---|---|
| `01_direct_prompt_injection.md` | Injection | 1 |
| `02_indirect_prompt_injection.md` | Injection | 2 |
| `03_tool_injection.md` | Injection | 3 |
| `04_multi_tenant_isolation.md` | Isolation | 4 |
| `05_namespace_isolation.md` | Isolation | 5 |
| `06_resource_memory_isolation.md` | Isolation | 6 |
| `07_session_isolation.md` | Isolation | 7 |
| `08_zero_trust_agentic.md` | Architecture | 8 |
| `09_capability_based_security.md` | Architecture | 9 |
| `10_capability_tokens.md` | Architecture | 10 |
| `11_sandboxing.md` | Architecture | 11 |
| `12_context_poisoning.md` | Logic | 12 |
| `13_tool_confusion.md` | Logic | 13 |
| `14_confused_deputy.md` | Logic | 14 |
