# Docker Image

A reproducible environment for the framework, the vulnerable
+ secure reference servers, and the experiment harness.

## Build

```bash
docker build -t mcp-iso -f artifact/docker/Dockerfile .
```

## Run

Three services are defined in `docker-compose.yml`:

```bash
docker compose -f artifact/docker/docker-compose.yml up analysis
```

This:

1. Builds the image (if not already built).
2. Runs `python -m analysis.scripts.run_all` inside the
   container, which regenerates the four
   `analysis/tables/rq*_summary.csv` files and the eight
   `analysis/figures/rq*_*.{pdf,png}` figures.
3. Mounts `analysis/` and `paper/` as volumes so the host can
   inspect the regenerated artefacts.

## Reproduce the paper

Inside the running container:

```bash
latexmk -pdf paper/main.tex
```

The PDF is written to `paper/main.pdf` in the host's working
directory (via the volume mount).

## Why this image

- **Pinned dependencies.** `requirements.txt` is the
  single source of truth for the Python toolchain. The
  image uses `pip install --no-cache-dir -r
  requirements.txt` to install them.
- **Pinned LaTeX.** `texlive-latex-base`,
  `texlive-latex-extra`, `texlive-fonts-recommended`, and
  `texlive-fonts-extra` are installed via `apt-get`. The
  `latexmk` and `biber` binaries come from the same
  metapackage.
- **No network at runtime.** The `RUN` instructions perform
  all installs at build time; the runtime container has no
  network requirement other than the volume mounts.