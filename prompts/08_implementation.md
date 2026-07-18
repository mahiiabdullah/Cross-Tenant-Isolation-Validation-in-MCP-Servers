# 08 â€” Implementation Prompt

> **Phase 8.** Write the code. Turn the Phase-6 framework design and the
> Phase-7 attack library into a runnable, tested Python package.

## Goal

Ship a working, version-controlled implementation of the framework, the MCP
server targets (vulnerable + secure), and the attack library â€” all reachable
via a single CLI entrypoint (`framework-cli`).

## Engineering Roadmap (4 sprints, 1 week each)

| Sprint | Theme                                  | Exit Criteria                                     |
|--------|----------------------------------------|---------------------------------------------------|
| S1     | Domain types & attack skeleton         | `pytest framework/core tests -q` green            |
| S2     | Vulnerable MCP server + fixture data   | `pytest mcp_servers/vulnerable tests -q` green    |
| S3     | Secure reference MCP server            | Defense table from `docs/06` mapped to code       |
| S4     | Orchestrator, metrics, dry-run harness | `framework-cli run --manifest demo.yaml` succeeds |

## Code-Generation Rules

1. **No file over 400 LoC.** Split when larger.
2. **Type hints everywhere.** `from __future__ import annotations` in every
   module; Pydantic v2 models for every cross-API boundary.
3. **No top-level side effects.** `import` must never mutate the filesystem.
   All I/O lives in `framework/utils/io.py`.
4. **Determinism.** Random sources seeded via
   `framework/utils/rand.py::seeded_rng(seed)`.
5. **Logging.** Every module instantiates `logger = logging.getLogger(__name__)`.
   Never `print()`.
6. **Errors.** Raise typed exceptions from `framework/core/errors.py`; no
   bare `Exception`.

## Vulnerable MCP Server (`mcp_servers/vulnerable/`)

A minimal but realistic MCP server with intentional isolation holes used as
the Phase-9 baseline:

- One transport per tenant, **shared** uvicorn worker (deliberate violation).
- Tools registered dynamically via a JSON file the operator writes (allows
  schema confusion).
- File-resource resolver follows **symlinks** (deliberate violation).
- No auth on the `list_tools` RPC.
- Cache layer keyed on `(tenant_id, tool_name)` only (no `prompt_hash` â†’
  poisoning trivially possible).

Each violation must be addressable via a `VulnFlags` env-flag so reviewers can
toggle a single hole on/off at runtime.

## Secure Reference Server (`mcp_servers/secure/`)

- One transport per tenant + per-session JWT + audience claim.
- Tools registered from a frozen, signed manifest (`security/manifest.sig`).
- File-resource resolver denies symlinks, requires read-only mount,
  enforces canonical paths.
- All IPC messages schema-validated with `jsonschema` before dispatch.
- Cache layer keyed on `(tenant_id, tool_name, prompt_hash, schema_version)`.

## Test Requirements

- Unit tests in `tests/` mirroring the `framework/` tree (mirror-only).
- â‰¥ 80 % line coverage on `framework/core/`, `framework/evaluator/`,
  `framework/metrics/`.
- One end-to-end integration test under `tests/integration/` exercising:
  vulnerable server + 3 attacks â†’ secure server + same 3 attacks.
- CI workflow at `.github/workflows/ci.yml` running `ruff`, `mypy`,
  `pytest --cov` on every push.

## Repo Deliverables

- Fully populated `framework/`, `attacks/`, `mcp_servers/` directories.
- `framework/cli.py` exposing:
  - `validate` (config & manifest linter)
  - `run` (execute an experiment manifest)
  - `report` (render results to Markdown / HTML)
- Locked `requirements.txt` and `requirements-dev.txt`.
- A `Makefile` with targets: `lint`, `typecheck`, `test`, `cov`, `run-demo`.

## Done When

- [ ] `make lint && make typecheck && make test` exits 0.
- [ ] `make run-demo` runs an end-to-end manifest in < 5 minutes and writes
      results to `analysis/runs/demo/`.
- [ ] Coverage report uploaded as build artifact.
- [ ] `README.md` "Quickstart" section reproduces `run-demo` from a clean
      clone.
- [ ] CHANGELOG.md entry per sprint (SemVer).