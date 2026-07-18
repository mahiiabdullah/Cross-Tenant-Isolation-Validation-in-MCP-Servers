"""Tiny loader for the Phase-9 runner outputs.

Provides :func:`load_results` which reads ``results.csv`` and
``meta.json`` for a given ``run_id`` and returns a
``(DataFrame, dict)`` pair.
"""

from __future__ import annotations

import json

import pandas as pd

from .. import REPO_ROOT


def load_results(run_id: str) -> tuple[pd.DataFrame, dict]:
    """Return ``(df, meta)`` for the given ``run_id``.

    The CSV columns are exactly those enumerated in
    ``experiments/runner.py:CSV_COLUMNS``.
    """
    run_dir = REPO_ROOT / "analysis" / "runs" / run_id
    csv_path = run_dir / "results.csv"
    meta_path = run_dir / "meta.json"
    if not csv_path.exists():
        raise FileNotFoundError(f"missing results.csv: {csv_path}")
    if not meta_path.exists():
        raise FileNotFoundError(f"missing meta.json: {meta_path}")
    df = pd.read_csv(csv_path)
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    return df, meta


def list_run_ids() -> list[str]:
    runs = REPO_ROOT / "analysis" / "runs"
    return sorted(
        p.name
        for p in runs.iterdir()
        if p.is_dir() and (p / "results.csv").exists()
    )


__all__ = ["load_results", "list_run_ids"]
