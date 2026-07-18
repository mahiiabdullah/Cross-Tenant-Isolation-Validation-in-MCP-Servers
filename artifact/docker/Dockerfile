# Dockerfile — Phase-12 artefact-evaluation image
#
# Builds a self-contained Python 3.11 environment that can
# reproduce every result in the paper. The image is the
# canonical USENIX artefact-evaluation entry point.

FROM python:3.11-slim

WORKDIR /workspace

# System dependencies for matplotlib + seaborn (LaTeX fonts).
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    latexmk \
    biber \
    git \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies (pinned).
COPY requirements.txt /workspace/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Repo.
COPY . /workspace

# Reproduce RQ-1..RQ-4 and render figures.
RUN python -m analysis.scripts.run_all

# Build the LaTeX manuscript.
WORKDIR /workspace
RUN latexmk -pdf paper/main.tex
RUN cp paper/main.pdf /workspace/main.pdf

CMD ["bash"]
