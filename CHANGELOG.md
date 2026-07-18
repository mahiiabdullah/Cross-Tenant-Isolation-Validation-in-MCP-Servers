# Changelog

All notable changes to the MCP Isolation Research project are
documented here. The format follows [Keep a Changelog](https://keepachangelog.com)
and the project adheres to [Semantic Versioning](https://semver.org/).

## [0.2.0] — Phase 8 (Implementation) — 2026-07-19

### Added
- Vulnerable reference MCP server (`mcp_servers/vulnerable/server.py`)
  with toggleable `VulnFlags` (dynamic tools, symlink follow,
  no-auth `list_tools`, shared cache key, shared transport).
- Secure reference MCP server (`mcp_servers/secure/server.py`)
  with per-tenant state, JWT auth (`aud` claim), frozen manifest,
  symlink-deny + canonical-path resolver, `prompt_hash` cache key.
- `framework/utils/io.py`, `framework/utils/rand.py`,
  `framework/core/errors.py` per the Phase-8 Code-Gen Rules.
- `framework/cli.py` exposing `validate`, `run`, `report`.
- `framework/target/connector.py:LocalServerConnector` — Phase-8
  in-process transport that talks to the reference servers.
- `Makefile` with `lint`, `typecheck`, `test`, `cov`,
  `run-demo`, `clean`.
- `requirements-dev.txt`.
- `experiments/manifests/demo.yaml` — minimal end-to-end
  manifest.
- `tests/test_framework_utils.py`, `tests/test_framework_errors.py`,
  `tests/test_vulnerable_server.py`, `tests/test_secure_server.py`,
  `tests/integration/test_end_to_end.py`.

### Changed
- `framework/__init__.py` version bumped to `0.2.0`.
- `framework/target/connector.py` — added `LocalServerConnector`
  alongside `DummyConnector`.

## [0.1.0] — Phases 1–7 — 2026-07-19

Initial release covering:
- Phase 1: 8 MCP isolation boundaries catalogued with 63 tickets.
- Phase 2: 14-concept security taxonomy with MCP-boundary bindings.
- Phase 3: 17 verified citations; related-work matrix.
- Phase 4: novelty doc (3 yes/no answers, score 8/10, 5
  contributions).
- Phase 5: per-boundary STRIDE tables + 4 misuse cases.
- Phase 6: framework harness (Scheduler, PayloadGenerator,
  MCPConnector, Evaluator, Metrics, Logger, Reporter) +
  end-to-end smoke test.
- Phase 7: 50 attack classes registered; CVSS-scored;
  pytest reproducible.