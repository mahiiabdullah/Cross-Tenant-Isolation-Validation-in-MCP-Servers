"""Experiment runner for Phase 9.

Reads a Phase-9 manifest, iterates over the (server_variant,
defense_level, attack) cells, and invokes the Phase-8 CLI once
per cell. Aggregates the per-cell ``events.jsonl`` files into a
single ``results.ndjson`` (one row per event) and a flat
``results.csv`` table, and writes ``meta.json`` with run
metadata.

Per the approved plan (do NOT redesign):
  - Reuse the Phase-8 CLI (``python framework/cli.py run ...``).
  - 30 iterations per cell via ``--iterations 30`` and
    ``--seed-offset`` for uniqueness.
  - Each cell gets a fresh output directory; the CLI emits
    ``events.jsonl`` into that directory which we read back.

Manifest extension over RunConfig:
  - ``run_id`` (str) — written to ``meta.json`` and every row.
  - ``iterations`` (int) — number of repetitions per cell.
  - ``servers`` (list[str]) — server variants to exercise.
  - ``defense_levels`` (list[str]) — defense levels to exercise.
    Allowed values: ``none``, ``partial`` / ``per_tenant``, ``full``.
  - ``attacks`` is the standard list of ``AttackRef`` dicts.
"""

from __future__ import annotations

import argparse
import csv
import json
import shlex
import subprocess
import sys
import time as _time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure the repo root is on sys.path when invoked as a script.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from framework.core.config import RunConfig  # noqa: E402
from framework.core.errors import ConfigError  # noqa: E402


# ---------------------------------------------------------------------------
# Manifest schema (Phase 9 extension over the Phase-6 RunConfig)
# ---------------------------------------------------------------------------


PHASE9_TOP_KEYS = {"run_id", "seed", "iterations", "servers", "defense_levels"}


def load_phase9_manifest(path: Path) -> dict[str, Any]:
    """Load the Phase-9 manifest and validate it minimally.

    The Phase-9 manifest is a superset of the Phase-6 ``RunConfig``
    YAML. We do a shallow schema check here; full pydantic
    validation happens after we inject the cell-specific fields.
    """
    import yaml  # local import; optional at the framework level

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ConfigError(f"manifest root must be a mapping (got {type(data).__name__})")
    for key in ("attacks", "tenants"):
        if key not in data:
            raise ConfigError(f"manifest missing required key: {key!r}")
    # Defaults for Phase-9 extensions.
    data.setdefault("run_id", f"exp-{datetime.now(timezone.utc):%Y-%m-%d-%H%M%S}")
    data.setdefault("seed", 42)
    data.setdefault("iterations", 30)
    data.setdefault("servers", ["vulnerable", "secure"])
    data.setdefault("defense_levels", ["none"])
    return data


def materialize_run_config(
    manifest: dict[str, Any],
    server: str,
    defense_level: str,
    seed_offset: int,
) -> RunConfig:
    """Build a Phase-6/8 ``RunConfig`` for one (server, defense) cell.

    ``defense_level`` ∈ {"none", "partial", "full"}. The flag
    values are derived from the level so that the underlying
    scheduler sees the right ``Defenses`` block.
    """
    defenses_flag = {
        "none": {
            "per_tenant_tool_registry": False,
            "tenant_prefixed_cache_keys": False,
            "resource_path_canonicalisation": False,
            "mtls": False,
        },
        "partial": {
            "per_tenant_tool_registry": True,
            "tenant_prefixed_cache_keys": False,
            "resource_path_canonicalisation": False,
            "mtls": False,
        },
        "per_tenant": {  # alias for "partial" used by RQ-4.
            "per_tenant_tool_registry": True,
            "tenant_prefixed_cache_keys": False,
            "resource_path_canonicalisation": False,
            "mtls": False,
        },
        "full": {
            "per_tenant_tool_registry": True,
            "tenant_prefixed_cache_keys": True,
            "resource_path_canonicalisation": True,
            "mtls": True,
        },
    }.get(defense_level)
    if defenses_flag is None:
        raise ConfigError(f"unknown defense_level: {defense_level!r}")

    # Begin from the manifest, overriding the defenses block with
    # the cell-specific flag set and bumping the seed by
    # `seed_offset` so each iteration is unique.
    cfg_dict: dict[str, Any] = {
        "run": {
            "seed": int(manifest["seed"]) + int(seed_offset),
            "repeats": 1,
            "concurrency": 2,
        },
        "tenants": manifest["tenants"],
        "attacks": manifest["attacks"],
        "defenses": defenses_flag,
        # The CLI ignores this for `--target` runs but keeps the
        # schema valid.
        "target": manifest.get("target", {"transport": "dummy"}),
        "output": {
            "log_dir": "experiments/logs",
            "output_dir": "experiments/outputs",
            "log_format": "jsonl",
        },
    }
    return RunConfig.model_validate(cfg_dict)


# ---------------------------------------------------------------------------
# Cell execution
# ---------------------------------------------------------------------------


def run_cell(
    *,
    server: str,
    defense_level: str,
    attack_ids: list[str],
    iterations: int,
    seed_offset: int,
    cell_dir: Path,
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    """Run a single (server, defense, attacks[]) cell.

    Invokes ``python framework/cli.py run <derived_manifest>
    --target <server> --output <cell_dir> --iterations <iterations>
    --seed-offset <seed_offset>`` and returns the aggregated
    list of event dicts emitted by the scheduler.
    """
    cell_dir.mkdir(parents=True, exist_ok=True)
    derived_manifest = cell_dir / "manifest.yaml"
    cfg = materialize_run_config(
        manifest=manifest,
        server=server,
        defense_level=defense_level,
        seed_offset=seed_offset,
    )
    # Write the derived RunConfig as YAML.
    import yaml

    derived_manifest.write_text(
        yaml.safe_dump(cfg.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )

    cmd = [
        sys.executable,
        str(_REPO_ROOT / "framework" / "cli.py"),
        "run",
        str(derived_manifest),
        "--target",
        server,
        "--output",
        str(cell_dir),
        "--iterations",
        str(iterations),
        "--seed-offset",
        "0",
    ]
    print(f"$ {' '.join(shlex.quote(p) for p in cmd)}", flush=True)
    rc = subprocess.run(cmd, cwd=str(_REPO_ROOT)).returncode
    if rc != 0:
        raise RuntimeError(f"cell failed (rc={rc}): {server}/{defense_level}")

    # Read the events.jsonl emitted by the CLI.
    events_path = cell_dir / "events.jsonl"
    if not events_path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in events_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        events.append(json.loads(line))
    return events


# ---------------------------------------------------------------------------
# Tagging + aggregation
# ---------------------------------------------------------------------------


CSV_COLUMNS = [
    "run_id",
    "iteration",
    "server_variant",
    "defense_level",
    "attack_id",
    "boundary",
    "event_type",
    "success",
    "latency_ms",
    "tenant_pair",
    "payload_sha256",
    "timestamp",
]


def _row_from_event(
    *,
    event: dict[str, Any],
    run_id: str,
    iteration: int,
    server_variant: str,
    defense_level: str,
) -> dict[str, Any]:
    """Flatten an event dict into a CSV row matching CSV_COLUMNS."""
    tenant_pair = event.get("tenant_pair") or []
    if isinstance(tenant_pair, list):
        tenant_pair_str = "|".join(str(t) for t in tenant_pair)
    else:
        tenant_pair_str = str(tenant_pair)
    return {
        "run_id": run_id,
        "iteration": iteration,
        "server_variant": server_variant,
        "defense_level": defense_level,
        "attack_id": event.get("attack_id", ""),
        "boundary": event.get("boundary", ""),
        "event_type": event.get("event_type", ""),
        "success": bool(event.get("success", False)),
        "latency_ms": event.get("latency_ms"),
        "tenant_pair": tenant_pair_str,
        "payload_sha256": event.get("payload_sha256", ""),
        "timestamp": event.get("timestamp", ""),
    }


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    """Write the aggregated events as a flat CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_ndjson(rows: list[dict[str, Any]], path: Path) -> None:
    """Write the aggregated events as newline-delimited JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, default=str) + "\n")


def _commit_sha() -> str:
    """Best-effort: return the current git commit SHA (short)."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# Top-level driver
# ---------------------------------------------------------------------------


def run_manifest(manifest_path: Path) -> int:
    """Run a single Phase-9 manifest end to end."""
    manifest_path = manifest_path.resolve()
    manifest = load_phase9_manifest(manifest_path)
    run_id = manifest["run_id"]
    iterations = int(manifest["iterations"])
    servers = list(manifest["servers"])
    defenses = list(manifest["defense_levels"])
    attack_ids = [a["id"] for a in manifest["attacks"]]

    run_dir = _REPO_ROOT / "analysis" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    cells_dir = run_dir / "cells"
    cells_dir.mkdir(parents=True, exist_ok=True)

    started_at = datetime.now(timezone.utc)
    t_start = _time.perf_counter()

    all_rows: list[dict[str, Any]] = []
    n_cells = 0
    # Iterate server × defense; iterations are inside the CLI.
    seed_running = 0
    for server in servers:
        for defense_level in defenses:
            n_cells += 1
            cell_name = f"{server}__{defense_level}"
            cell_dir = cells_dir / cell_name
            events = run_cell(
                server=server,
                defense_level=defense_level,
                attack_ids=attack_ids,
                iterations=iterations,
                seed_offset=seed_running,
                cell_dir=cell_dir,
                manifest=manifest,
            )
            seed_running += iterations
            # We don't know which iteration a given event came
            # from (the CLI aggregates them) so we tag all events
            # in the cell with iteration=0. Phase 10 splits by
            # cell anyway, so this is sufficient.
            for ev in events:
                all_rows.append(
                    _row_from_event(
                        event=ev,
                        run_id=run_id,
                        iteration=0,
                        server_variant=server,
                        defense_level=defense_level,
                    )
                )

    duration_s = _time.perf_counter() - t_start
    ended_at = datetime.now(timezone.utc)

    # Materialize outputs.
    write_ndjson(all_rows, run_dir / "results.ndjson")
    write_csv(all_rows, run_dir / "results.csv")
    meta = {
        "run_id": run_id,
        "manifest": str(manifest_path.relative_to(_REPO_ROOT)),
        "manifest_abs": str(manifest_path),
        "commit_sha": _commit_sha(),
        "seed": int(manifest["seed"]),
        "iterations": iterations,
        "servers": servers,
        "defense_levels": defenses,
        "attacks": attack_ids,
        "n_cells": n_cells,
        "n_events": len(all_rows),
        "duration_s": round(duration_s, 3),
        "started_at": started_at.isoformat(),
        "ended_at": ended_at.isoformat(),
    }
    (run_dir / "meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )

    print(
        f"runner: run_id={run_id} cells={n_cells} events={len(all_rows)} "
        f"duration_s={duration_s:.2f}"
    )
    print(f"runner: wrote {run_dir / 'results.ndjson'}")
    print(f"runner: wrote {run_dir / 'results.csv'}")
    print(f"runner: wrote {run_dir / 'meta.json'}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="experiments.runner",
        description=__doc__,
    )
    p.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="path to a Phase-9 manifest YAML",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    return run_manifest(args.manifest)


if __name__ == "__main__":
    sys.exit(main())
