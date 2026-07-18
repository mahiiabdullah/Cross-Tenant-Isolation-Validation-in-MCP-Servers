# 02 — Security Learning Prompt

> **Phase 2.** Establish the theoretical foundation of every attack class the
> project will use. Acting as a specialist in AI systems security.

## Goal

Construct a formal taxonomy mapping established security vulnerabilities to
the LLM/Agent ecosystem, and pin each concept to a specific MCP boundary.

## Output Structure (per concept)

- **(A) Formal Definition.** Cite a primary source (RFC, CWE, academic paper).
- **(B) Threat Model.** Attacker position, assets, preconditions.
- **(C) Real-World / Theoretical Example.** Concrete scenario.
- **(D) Standard Defenses.** What the community considers "known good."
- **(E) Open Research Problems.** Why this still matters.
- **(F) Direct Relation to MCP Architecture.** Specific boundary and primitive.

## Concept Coverage

### Injection

- Direct prompt injection.
- Indirect prompt injection (via tool results / resources).
- Tool injection (malicious or shadow tools).

### Isolation

- Multi-tenant isolation.
- Namespace isolation.
- Resource / memory isolation.
- Session isolation.

### Architecture

- Zero Trust in agentic systems.
- Capability-based security.
- Capability tokens.
- Sandboxing (WASM, gVisor, Firecracker, OS process isolation).

### Logic

- Context poisoning.
- Tool confusion (routing ambiguity).
- Confused deputy problem.

## Style

- Concise, academic register. Clear markdown headers.
- One concept = one subsection. No merging.
- No invented citations; mark unverifiable claims as *"requires verification."*

## Repo Deliverables

- Per-concept notes in `docs/notes/security_learning/`.
- Cross-links inserted into `literature/related_work.md` where a concept maps
  to a known paper.
- Taxonomy figure `docs/diagrams/security_taxonomy.{dot,svg}`.

## Done When

- [ ] All 13 concepts have A–F.
- [ ] Each concept has at least one concrete MCP binding in (F).
