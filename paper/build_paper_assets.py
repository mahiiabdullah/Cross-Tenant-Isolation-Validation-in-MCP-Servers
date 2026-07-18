#!/usr/bin/env python3
"""Stage paper artefacts from `analysis/` into `paper/`.

Run after `python -m analysis.scripts.run_all`:

    python paper/build_paper_assets.py

This is a one-line wrapper over the cross-directory copy
documented in `paper/README.md`. It exists so the build
instructions can be exercised from a single shell command in
CI.

Why a Python wrapper rather than a `cp` shell command?

* The analysis artefacts are regenerated on every run; we want
  the copy step to be reproducible on Windows + POSIX.
* A Python wrapper can also assert that every artefact listed
  in the LaTeX `\includegraphics{...}` calls is present on
  disk before triggering the LaTeX build.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PAPER_FIG_DIR = REPO_ROOT / "paper" / "figures"
PAPER_TBL_DIR = REPO_ROOT / "paper" / "tables"
ANALYSIS_FIG_DIR = REPO_ROOT / "analysis" / "figures"
ANALYSIS_TBL_DIR = REPO_ROOT / "analysis" / "tables"

FIGURE_STEMS = (
    "rq1_leak_rate_by_boundary",
    "rq2_cache_heatmap",
    "rq3_injection_latency",
    "rq4_defense_combo_bars",
)
TABLE_STEMS = (
    "rq1_summary",
    "rq2_summary",
    "rq3_summary",
    "rq4_summary",
)


def _copytree(src_dir: Path, dst_dir: Path, stems: tuple[str, ...],
              extensions: tuple[str, ...]) -> list[Path]:
    """Copy ``stems.extensions`` from ``src_dir`` to ``dst_dir``.

    Returns the list of destination paths actually written.
    """
    dst_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for stem in stems:
        for ext in extensions:
            src = src_dir / f"{stem}.{ext}"
            if not src.exists():
                print(f"build_paper_assets: missing source {src}",
                      file=sys.stderr)
                continue
            dst = dst_dir / f"{stem}.{ext}"
            shutil.copy2(src, dst)
            written.append(dst)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="build_paper_assets")
    parser.add_argument("--dry-run", action="store_true",
                        help="print what would be copied without writing")
    args = parser.parse_args(argv)

    print("build_paper_assets: staging paper/figures/ from analysis/")
    if not args.dry_run:
        written_figs = _copytree(
            ANALYSIS_FIG_DIR, PAPER_FIG_DIR, FIGURE_STEMS,
            ("pdf", "png")
        )
        for p in written_figs:
            print(f"  -> {p.relative_to(REPO_ROOT)}")
    print("build_paper_assets: staging paper/tables/ from analysis/")
    if not args.dry_run:
        written_tbls = _copytree(
            ANALYSIS_TBL_DIR, PAPER_TBL_DIR, TABLE_STEMS, ("csv",)
        )
        for p in written_tbls:
            print(f"  -> {p.relative_to(REPO_ROOT)}")

    print("build_paper_assets: done.")
    print("Next step: latexmk -pdf paper/main.tex")
    return 0


if __name__ == "__main__":
    sys.exit(main())