# 07 â€” Attack Library Prompt

> **Phase 7.** Build a reproducible attack library covering every Trust-Boundary
> crossing the Phase-5 DFD identified.

## Goal

Produce a curated, executable set of attack classes â€” one concrete instantiation
per (Boundary Ã— STRIDE category Ã— Trust-Originator pair) â€” that the framework
can run unattended. Each attack is a small, single-responsibility Python class
that inherits from `attacks/base.py::Attack`.

## Macro Categories

| # | Category                | What it stresses                                           |
|---|-------------------------|------------------------------------------------------------|
| 1 | Direct Prompt Injection | Cross-tenant data leak via prompt/content smuggling        |
| 2 | Isolation Break         | Two tenants reach each other's namespace or tool registry |
| 3 | Architectural Confusion | Mistaken authority through ambiguous MCP routing / schemas |
| 4 | Logic / State Abuse     | Long-tail semantic exploits (auth replay, cache poisoning) |

## Output Structure (per attack class)

1. **Header** â€” class identity:
   - File path under `attacks/<boundary>/<attack_id>.py`
   - Class name `<AttackId>Attack(Attack)`
   - `id`, `boundary`, `name`, `description`, `severity` (CVSS v3.1)
2. **Per-class `Attack` method contract** â€” must implement:
   - `setup(env) -> None`
   - `execute(session: Session, tenant_a: Tenant, tenant_b: Tenant) -> AttackResult`
   - `teardown(env) -> None`
3. **Test contract** â€” every attack ships with one pytest under
   `attacks/<boundary>/tests/test_<attack_id>.py` proving:
   - it executes without raising
   - it returns `AttackResult(leaked=True/False, ...)` deterministically
4. **Provenance** â€” top-of-file comment citing the Phase-5 misuse case and
   the literature entry from `literature/related_work.md` that informed it.

## Per-Attack Checklist (required fields)

- [ ] `id` matches `^A-[A-Z]{2,4}-\d{3}$` (e.g. `A-TRN-001` for transport)
- [ ] `boundary` âˆˆ `framework/core/types.py::Boundary`
- [ ] Files written: `attacks/<boundary>/<id>.py`,
      `attacks/<boundary>/tests/test_<id>.py`
- [ ] Severity scored via `analysis/severity.py::cvss_v31()`
- [ ] One-line entry in `attacks/INDEX.md`
- [ ] Linked from the Phase-5 misuse-case table
- [ ] Reproducible: `pytest attacks/<boundary>/tests/test_<id>.py` passes

## Repo Deliverables

- `attacks/base.py` extended with any shared helpers (e.g. `PromptSmuggler`,
  `ToolDescriptorFaker`) discovered during implementation.
- New sub-package per Boundary value:
  `attacks/{transport,session,namespace,tool,resource,memory,cache,auth}/`
- `attacks/INDEX.md` â€” human-readable catalogue (table: id, boundary, name,
  severity, success rate).
- `experiments/manifests/attacks.yaml` â€” list of attack ids selected for the
  final evaluation run, with per-attack iteration counts.

## Done When

- [ ] â‰¥ 25 attack classes implemented across â‰¥ 6 different `Boundary` values.
- [ ] Every attack has a passing unit test.
- [ ] `attacks/INDEX.md` cross-links to the misuse-case table in
      `docs/05_Attack_Taxonomy.md`.
- [ ] `pytest attacks/ -q` exits 0.
- [ ] `experiments/manifests/attacks.yaml` lists a balanced subset (â‰¥ 3 attacks
      per chosen boundary) for the main study.