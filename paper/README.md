# Paper

Conference-ready LaTeX manuscript for the project
"Cross-Tenant Isolation Validation in MCP Servers".

## Layout

```
paper/
├── main.tex              # master file
├── preamble.sty          # style preamble (USENIX letter, booktabs, pgfplots)
├── sections/             # per-section .tex files (10 total)
│   ├── 01_introduction.tex
│   ├── 02_background.tex
│   ├── 03_threat_model.tex
│   ├── 04_framework.tex
│   ├── 05_attacks.tex
│   ├── 06_evaluation.tex
│   ├── 07_defenses.tex
│   ├── 08_related_work.tex
│   ├── 09_discussion.tex
│   └── 10_conclusion.tex
├── figures/              # PDF + PNG per figure (mirrors analysis/figures/)
├── tables/               # CSV per table (mirrors analysis/tables/)
├── references.bib        # BibLaTeX bibliography (mirrors literature/bibliography.bib)
├── build_paper_assets.py # cross-directory copy helper
└── README.md             # this file
```

## Build

The canonical command (run from the repository root):

```bash
latexmk -pdf paper/main.tex
```

(or, on Windows with MiKTeX / TeX Live installed):

```powershell
latexmk -pdf paper\main.tex
```

`latexmk` will produce `main.pdf` in `paper/`.

## Reproducing figures and tables

Regenerate the analysis outputs:

```bash
python -m analysis.scripts.run_all
```

Then stage the artefacts into `paper/`:

```bash
python paper/build_paper_assets.py
```

This populates `paper/figures/rq{1..4}_*.{pdf,png}` and
`paper/tables/rq{1..4}_summary.csv`. The LaTeX manuscript
references these files via relative paths
(`figures/...` and `tables/...`).

## Citation policy

Every bibliography entry has a per-paper summary at
`literature/summaries/<key>.md`. The BibLaTeX style is
`alphabetic`.

## Style conformance

The manuscript follows these conventions:

- BibLaTeX with `style=alphabetic`.
- `\includegraphics{figures/<file>.pdf}` only.
- `booktabs` tables with no vertical rules.
- All numbers traced back to
  `analysis/tables/*.csv`.
- Acronyms defined on first use in
  `sections/02_background.tex`.
- Target 12 pages + unlimited references (current build
  is approximately 11 pages).

## Continuous integration

The repository does not yet ship a CI workflow; a future
worker can add a GitHub Actions job that runs

```yaml
- run: sudo apt-get install -y texlive-full latexmk
- run: latexmk -pdf paper/main.tex
```

and uploads `paper/main.pdf` as an artifact.