"""Programmatically assemble the Phase-10 Jupyter notebooks.

Each notebook follows the documented convention:

1. Cell 1 = provenance (run_id, commit_sha, dataset version,
   seed).
2. Cell 2 = load + assert schema + row count.
3. Analysis cells = one per research question, each emitting
   a CSV in ``tables/`` and a figure in ``figures/``.
4. Last cell = markdown bullets reused verbatim in
   ``paper/sections/06_evaluation.tex``.

Notebooks are reconstructed from scratch on every run; they
delegate their work to ``analysis.scripts.run_all`` /
``analysis.scripts.plots`` so the same logic is exercised
whether the user runs ``python -m analysis.scripts.build_notebooks``
or executes the notebook via ``jupyter nbconvert --execute``.

Run once after editing the source:
    python -m analysis.scripts.build_notebooks
"""

from __future__ import annotations

import sys
from pathlib import Path

import nbformat as nbf
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

from .. import ANALYSIS_DIR
from .load_runs import list_run_ids

NOTEBOOKS_DIR = ANALYSIS_DIR / "notebooks"


def _provenance_cell(run_id: str) -> str:
    meta_line = (
        "import json, sys\n"
        "from pathlib import Path\n"
        f"run_id = {run_id!r}\n"
        "# Ensure the repo root is importable when the notebook\n"
        "# is executed by nbconvert from the notebooks/ directory.\n"
        "_root = Path.cwd()\n"
        "while not (_root / 'pyproject.toml').exists() and _root != _root.parent:\n"
        "    _root = _root.parent\n"
        "if str(_root) not in sys.path:\n"
        "    sys.path.insert(0, str(_root))\n"
        "from analysis import REPO_ROOT\n"
        "meta_path = REPO_ROOT / 'analysis' / 'runs' / run_id / 'meta.json'\n"
        "meta = json.loads(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}\n"
        "print('run_id          :', meta.get('run_id', run_id))\n"
        "print('commit_sha      :', meta.get('commit_sha', 'unknown'))\n"
        "print('seed            :', meta.get('seed', 'n/a'))\n"
        "print('iterations      :', meta.get('iterations', 'n/a'))\n"
        "print('servers         :', meta.get('servers', 'n/a'))\n"
        "print('defense_levels  :', meta.get('defense_levels', 'n/a'))\n"
        "print('attacks         :', meta.get('attacks', 'n/a'))\n"
        "print('n_events        :', meta.get('n_events', 'n/a'))\n"
        "print('duration_s      :', meta.get('duration_s', 'n/a'))\n"
    )
    return meta_line


def _sys_path_setup() -> str:
    """Snippet prepended to every code cell so the notebook can
    import the ``analysis`` package from a vanilla kernel.
    """
    return (
        "import sys\n"
        "from pathlib import Path as _P\n"
        "_root = _P.cwd()\n"
        "while not (_root / 'pyproject.toml').exists() and _root != _root.parent:\n"
        "    _root = _root.parent\n"
        "if str(_root) not in sys.path:\n"
        "    sys.path.insert(0, str(_root))\n"
    )


def _write_notebook(path: Path, cells: list) -> None:
    nb = new_notebook(
        cells=cells,
        metadata={
            "kernelspec": {
                "name": "python3",
                "display_name": "Python 3",
                "language": "python",
            },
            "language_info": {"name": "python"},
        },
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(nbf.writes(nb), encoding="utf-8")
    print(f"build_notebooks: wrote {path}")


def build_01_loading(run_id: str) -> Path:
    setup = _sys_path_setup()
    cells = [
        new_markdown_cell("# 01 — Loading & Cleaning\n\nProvenance + schema check for the requested run."),
        new_code_cell(
            setup +
            "import pandas as pd\n"
            f"run_id = {run_id!r}\n"
            "from analysis.scripts.load_runs import load_results\n"
            "df, meta = load_results(run_id)\n"
            "display(df.head())\n"
            "print('rows:', len(df))\n"
            "expected = {'run_id','iteration','server_variant','defense_level','attack_id','boundary','event_type','success','latency_ms','tenant_pair','payload_sha256','timestamp'}\n"
            "missing = expected - set(df.columns)\n"
            "extra   = set(df.columns) - expected\n"
            "assert not missing, f'missing columns: {missing}'\n"
            "print('schema OK; extra columns (ignored):', sorted(extra))"
        ),
    ]
    path = NOTEBOOKS_DIR / "01_loading_and_cleaning.ipynb"
    _write_notebook(path, cells)
    return path


def build_02_rq1(run_id: str) -> Path:
    setup = _sys_path_setup()
    cells = [
        new_markdown_cell("# 02 — RQ-1 Baseline isolation\n\nWelch's t-test + Cliff's δ on vulnerable vs. secure."),
        new_code_cell(_provenance_cell(run_id)),
        new_code_cell(
            setup +
            "from analysis.scripts.run_all import rq1_summary\n"
            "from analysis.scripts.load_runs import load_results\n"
            f"run_id = {run_id!r}\n"
            "df, _ = load_results(run_id)\n"
            "table = rq1_summary(df)\n"
            "display(table)\n"
            "print('global Welch t =', table.attrs.get('global_welch_t'))\n"
            "print('global Welch p =', table.attrs.get('global_welch_p'))\n"
            "print('global Cliff δ =', table.attrs.get('global_cliffs_delta'))"
        ),
    ]
    path = NOTEBOOKS_DIR / "02_rq1_baseline.ipynb"
    _write_notebook(path, cells)
    return path


def build_03_rq2(run_id: str) -> Path:
    setup = _sys_path_setup()
    cells = [
        new_markdown_cell("# 03 — RQ-2 Cache dominance\n\nOne-sided z-test on vulnerable-server leak volume."),
        new_code_cell(_provenance_cell(run_id)),
        new_code_cell(
            setup +
            "from analysis.scripts.run_all import rq2_summary\n"
            "from analysis.scripts.load_runs import load_results\n"
            f"run_id = {run_id!r}\n"
            "df, _ = load_results(run_id)\n"
            "table = rq2_summary(df)\n"
            "display(table)\n"
            "print('headline z =', table.attrs.get('headline_z'))\n"
            "print('headline p =', table.attrs.get('headline_p'))\n"
            "print('cache share =', table.attrs.get('cache_share_overall'))"
        ),
    ]
    path = NOTEBOOKS_DIR / "03_rq2_cache.ipynb"
    _write_notebook(path, cells)
    return path


def build_04_rq3(run_id: str) -> Path:
    setup = _sys_path_setup()
    cells = [
        new_markdown_cell("# 04 — RQ-3 Prompt-injection residual\n\nSecure-server latency + bounded-residual check."),
        new_code_cell(_provenance_cell(run_id)),
        new_code_cell(
            setup +
            "from analysis.scripts.run_all import rq3_summary\n"
            "from analysis.scripts.load_runs import load_results\n"
            f"run_id = {run_id!r}\n"
            "df, _ = load_results(run_id)\n"
            "table = rq3_summary(df)\n"
            "display(table)"
        ),
    ]
    path = NOTEBOOKS_DIR / "04_rq3_injection.ipynb"
    _write_notebook(path, cells)
    return path


def build_05_rq4(run_id: str) -> Path:
    setup = _sys_path_setup()
    cells = [
        new_markdown_cell("# 05 — RQ-4 Defense combo super-additivity\n\nPaired Welch's t on (partial − full) leakage differences."),
        new_code_cell(_provenance_cell(run_id)),
        new_code_cell(
            setup +
            "from analysis.scripts.run_all import rq4_summary\n"
            "from analysis.scripts.load_runs import load_results\n"
            f"run_id = {run_id!r}\n"
            "df, _ = load_results(run_id)\n"
            "table = rq4_summary(df)\n"
            "display(table)\n"
            "print('paired t =', table.attrs.get('paired_t'))\n"
            "print('paired p =', table.attrs.get('paired_p'))"
        ),
    ]
    path = NOTEBOOKS_DIR / "05_rq4_defense_combo.ipynb"
    _write_notebook(path, cells)
    return path


def build_06_summary() -> Path:
    setup = _sys_path_setup()
    rq1_run = "exp-rq1-baseline"
    rq2_run = "exp-rq2-cache"
    rq3_run = "exp-rq3-injection"
    rq4_run = "exp-rq4-defense"
    cells = [
        new_markdown_cell(
            "# 06 — Summary findings\n\n"
            "Verbatim bullets reused in "
            "`paper/sections/06_evaluation.tex`."
        ),
        new_code_cell(
            setup +
            "from analysis import ANALYSIS_DIR\n"
            "print((ANALYSIS_DIR / 'SUMMARY.md').read_text(encoding='utf-8'))"
        ),
        new_markdown_cell(
            f"- RQ-1 run_id: `{rq1_run}`\n"
            f"- RQ-2 run_id: `{rq2_run}`\n"
            f"- RQ-3 run_id: `{rq3_run}`\n"
            f"- RQ-4 run_id: `{rq4_run}`\n"
        ),
    ]
    path = NOTEBOOKS_DIR / "06_summary_findings.ipynb"
    _write_notebook(path, cells)
    return path


def build_all() -> None:
    runs = list_run_ids()
    if "exp-rq1-baseline" not in runs:
        print("warning: exp-rq1-baseline not in list_run_ids()")
    build_01_loading("exp-rq1-baseline")
    build_02_rq1("exp-rq1-baseline")
    build_03_rq2("exp-rq2-cache")
    build_04_rq3("exp-rq3-injection")
    build_05_rq4("exp-rq4-defense")
    build_06_summary()


def main(argv: list[str] | None = None) -> int:
    build_all()
    return 0


if __name__ == "__main__":
    sys.exit(main())