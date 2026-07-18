# Reproduction

Step-by-step instructions to reproduce the paper's main results
from a clean machine.

## Quick start (Docker)

```bash
git clone https://github.com/<org>/mcp-isolation-research
cd mcp-isolation-research
docker compose -f artifact/docker/docker-compose.yml up analysis
```

This regenerates `analysis/tables/*.csv` and
`analysis/figures/*.{pdf,png}` inside the container.

## Manual reproduction (host Python 3.10+)

```bash
# 1. Install pinned dependencies.
pip install -r requirements.txt

# 2. (Optional) Re-run the Phase-9 experiment harness.
#    This step requires the vulnerable + secure servers to be
#    built and the manifests to be present.
python -m experiments.runner --manifest experiments/manifests/rq1_baseline.yaml
python -m experiments.runner --manifest experiments/manifests/rq2_cache.yaml
python -m experiments.runner --manifest experiments/manifests/rq3_injection.yaml
python -m experiments.runner --manifest experiments/manifests/rq4_defense.yaml

# 3. Run the Phase-10 analysis driver.
python -m analysis.scripts.run_all

# 4. (Optional) Execute the Jupyter notebooks.
jupyter nbconvert --to notebook --execute analysis/notebooks/*.ipynb --inplace

# 5. Stage the artefacts into the paper.
python paper/build_paper_assets.py

# 6. Build the LaTeX manuscript.
latexmk -pdf paper/main.tex
```

## Inspecting the outputs

After step 5:

- `paper/tables/rq{1..4}_summary.csv` — the four summary tables
  (Section 6).
- `paper/figures/rq{1..4}_*.{pdf,png}` — the four figures
  (Section 6).

After step 6:

- `paper/main.pdf` — the compiled manuscript.

## Verifying reproducibility

The full reproducibility log (machines, commands, hashes) is
in `paper/appendix_b_reproduction_log.md`.

## What is NOT in scope

- The Phase-9 experiment harness (step 2) is slow (~30 min per
  manifest on a single core). The pre-computed CSVs in
  `analysis/runs/` are the canonical numbers; step 2 is for
  re-validation only.
- The LaTeX build (step 6) requires `texlive-full` (~3 GB);
  the Docker image in `artifact/docker/Dockerfile` is the
  canonical entry point for users without a local TeX
  install.