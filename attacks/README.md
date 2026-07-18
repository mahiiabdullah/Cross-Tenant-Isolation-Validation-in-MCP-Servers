# Attack Library

> **Phase 5 stub library; Phase 7 will fill in concrete `execute()`
> bodies.** Source of truth for the STRIDE-per-boundary mapping:
> `docs/04_Attack_Taxonomy.md`. Cross-reference for ticket IDs:
> `docs/notes/mcp_learning/00_appendix.md`.

## Status

Phase 5 produces **48 stub files** (8 boundaries × 6 STRIDE letters).
Each stub:

- subclasses `attacks.base.Attack` (see `base.py`);
- sets `id` to a STRIDE-row identifier of the form
  `"A-{PREFIX}-{LETTER}"` (e.g. `"A-TRN-S"` for the transport
  boundary's spoofing row);
- sets `boundary` to a `Boundary` enum value;
- raises `NotImplementedError` from `setup`, `execute`, and
  `teardown`, with a docstring pointing back to
  `docs/04_Attack_Taxonomy.md`.

## Layout

```
attacks/
  __init__.py
  base.py                       # Attack base + AttackResult dataclass
  transport/                    # transport boundary stubs
  session/                      # session boundary stubs
  namespace/                    # namespace boundary stubs
  tools/                        # tool boundary stubs
  resources/                    # resource boundary stubs
  memory/                       # memory boundary stubs
  cache/                        # cache boundary stubs
  auth/                         # auth boundary stubs
  fuzzing/                      # property / grammar-based fuzzing (Phase 7)
  prompt_injection/             # cross-cutting prompt injection (Phase 7)
```

## Stub Conventions

- File names: `a_<boundary>_<letter>.py` (e.g.
  `attacks/transport/a_transport_s.py`).
- Class names: `PascalCase(boundary_enum) + Letter + "Attack"`
  (e.g. `TransportSAttack`, `ResourceTAttack`).
- `id` format: `"A-{TRN|SES|NSP|TOL|RES|MEM|CCH|AUT}-{S|T|R|I|D|E}"`.
- `boundary` set via `Boundary.{TRANSPORT|SESSION|NAMESPACE|TOOL|RESOURCE|MEMORY|CACHE|AUTH}`.
- All three lifecycle methods raise `NotImplementedError` until
  Phase 7.

## Phase 7 Contract

Phase 7 will replace each `NotImplementedError` with a concrete
`execute()` that:

1. Sets up any preconditions (e.g. spawns two tenants, primes a
   cache).
2. Runs the attack against the configured MCP server
   (vulnerable / secure reference pair from Phase 8).
3. Returns an `AttackResult(success=bool, boundary=..., detail={...})`
   where `detail` includes the ticket IDs cross-referenced from
   the STRIDE row in `docs/04_Attack_Taxonomy.md`.

## Cross-References

- STRIDE table: `docs/04_Attack_Taxonomy.md` (8 per-boundary tables).
- Misuse cases: `docs/04_Attack_Taxonomy.md` (MC-1 through MC-4).
- Ticket index: `docs/notes/mcp_learning/00_appendix.md`.
- Threat model: `docs/02_Threat_Model.md`.
- Framework types: `framework/core/types.py` (`Boundary` enum).