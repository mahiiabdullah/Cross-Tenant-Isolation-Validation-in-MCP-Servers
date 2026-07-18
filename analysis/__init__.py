"""Analysis package.

Re-exports a few canonical paths so submodules don't have to
re-derive them.
"""

from __future__ import annotations

from pathlib import Path

# D:\CUET\Paper\mcp-isolation-research
REPO_ROOT = Path(__file__).resolve().parent.parent
ANALYSIS_DIR = REPO_ROOT / "analysis"
TABLES_DIR = ANALYSIS_DIR / "tables"
FIGURES_DIR = ANALYSIS_DIR / "figures"
RUNS_DIR = ANALYSIS_DIR / "runs"

__all__ = [
    "ANALYSIS_DIR",
    "FIGURES_DIR",
    "REPO_ROOT",
    "RUNS_DIR",
    "TABLES_DIR",
]