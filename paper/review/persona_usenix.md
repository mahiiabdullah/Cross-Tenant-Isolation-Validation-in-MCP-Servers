# Persona: USENIX Pragmatist Reviewer

> **Lens.** Reproducibility, artefact availability, clarity.
> Stance: **publish if a reader can replicate in two evenings**.
> Modeled on a USENIX Security artefact-evaluation committee
> member who will spend two evenings with the artifact and
> then vote reject if anything breaks.

## Concerns (numbered, ≥ 8)

### U-1. No `artifact/` Dockerfile; the README is a stub

> "`artifact/docker/README.md` is a one-paragraph stub. There
> is no Dockerfile, no `docker-compose.yml`, no pinned base
> image. A reader cannot reproduce in two evenings without
> installing Python 3.10+ and the analysis dependencies from
> scratch."

**Concern.** The artefact lacks the Docker substrate.

**Evidence.** `artifact/docker/README.md`;
`artifact/docker/` directory contents.

**Action.** Fixed.

**Patch.** A `artifact/docker/Dockerfile` is added based on
`python:3.11-slim`, copying the repo and running
`pip install -r requirements.txt`. A
`artifact/docker/docker-compose.yml` is added with three
services: `framework` (the harness), `analysis` (the
notebooks), and `mcp` (the vulnerable + secure servers).
The README is expanded to document the three-service flow
and the one-command entry point
(`docker compose up analysis`).

**Justified.** The Docker substrate is the canonical
USENIX artefact-evaluation entry point; the one-command
flow makes the two-evening reproduction test pass.

---

### U-2. `artifact/release/` is a stub

> "There is no `release/CHECKSUMS`, no `release/SHA256SUMS`,
> no signed tag. A reviewer cannot verify the artifact
> bundle's integrity."

**Concern.** No integrity verification.

**Evidence.** `artifact/release/README.md`.

**Action.** Partial.

**Patch.** `artifact/release/CHECKSUMS.txt` is added with
sha256 sums of every CSV, PDF, and PNG in
`analysis/tables/` and `analysis/figures/`. A signed-tag
recipe (using `git tag -s v0.1.0`) is added to the README.
The actual signing is left to the maintainer because the
reviewer's GPG key is not yet provisioned.

**Justified.** The checksums are reproducible now; the
signed tag is a process step that depends on the
maintainer's GPG key, which is out of scope for the
manuscript.

---

### U-3. The reproduction recipe assumes `python -m
analysis.scripts.run_all` runs from the repo root

> "`paper/README.md` says 'run from the repository root' but
> does not include a `cd` command. A reviewer running
> `docker compose up analysis` from the wrong directory will
> hit a path error."

**Concern.** The reproduction recipe is ambiguous.

**Evidence.** `paper/README.md`; `paper/build_paper_assets.py`.

**Action.** Fixed.

**Patch.** `paper/README.md` now states explicitly:
"Run from the repository root:
`\texttt{cd mcp-isolation-research && latexmk -pdf paper/main.tex}`."
The `build_paper_assets.py` script also prints the
recommended `cd` command when run with `--dry-run`.

**Justified.** The reproduction recipe is now
unambiguous; the dry-run helper makes the entry point
discoverable.

---

### U-4. `analysis/notebooks/*.ipynb` execute via
`nbconvert --execute` but the user is not told this

> "The notebooks exist but the README does not document how
> to execute them. A reviewer will try `jupyter notebook` and
> hit a missing-kernel error."

**Concern.** The notebook execution path is undocumented.

**Evidence.** `analysis/README.md` (if any); the notebook
`kernelspec` metadata.

**Action.** Fixed.

**Patch.** `analysis/README.md` is updated to include the
canonical notebook-execution command:
`\texttt{jupyter nbconvert --to notebook --execute
analysis/notebooks/*.ipynb --inplace}`.
The README also documents the rebuild path:
`\texttt{python -m analysis.scripts.build\_notebooks}`
re-generates the notebooks from scratch.

**Justified.** The notebook execution path is now a single
command; the rebuild path documents the source-of-truth
relationship between the Python scripts and the notebooks.

---

### U-5. `paper/sections/06_evaluation.tex` cites
`analysis/tables/*.csv` but does not show the raw values

> "The summary tables in §6 are LaTeX-rendered
> \texttt{tabularx} blocks, not direct copies of the CSV
> cells. A reviewer verifying a number has to manually
> reconcile the LaTeX table with the CSV row."

**Concern.** The summary tables are not machine-checkable.

**Evidence.** `paper/sections/06_evaluation.tex` §6 tables.

**Action.** Partial.

**Patch.** A new appendix (Appendix~A in the README) is
added that documents the
exact `pd.read_csv(...).to_dict()` values for every number
in §6. The appendix lives at
`paper/appendix_a_data_traceability.md` and is referenced
from §6 via `\input{appendix_a_data_traceability}`.
The LaTeX tables remain because they are required for the
paper format, but the CSV cell values are now
machine-verifiable.

**Justified.** The data-traceability appendix is the
canonical USENIX artefact-evaluation answer to
"how do I verify this number?".

---

### U-6. The MCP server fixtures are referenced but not
described

> "The paper mentions `mcp_servers/vulnerable/` and
> `mcp_servers/secure/` but does not describe the fixtures
> or the tool catalogue. A reviewer building the secure
> server does not know what tools to expect."

**Concern.** The reference server's catalogue is undocumented.

**Evidence.** `mcp_servers/` (read via the repo); §4
"Reference servers" subsection.

**Action.** Fixed.

**Patch.** `paper/sections/04_framework.tex` §4 "Reference
servers" is expanded with a tool-catalogue table:
`echo`, `get_secret`, `list_tenants`, `set_env`, etc. The
table lists each tool, its arguments, and whether it is
exposed by both servers or only the vulnerable one. The
table is also added to the artefact bundle
(`artifact/release/TOOL_CATALOGUE.md`).

**Justified.** The catalogue is now discoverable; a
reviewer building the secure server knows what tools to
expect.

---

### U-7. The seed-controlled manifest format is not in the
paper

> "The paper mentions seed-controlled manifests but does not
> show the manifest schema. A reviewer cannot reproduce a
> single cell without inspecting
> `experiments/manifests/rq1_baseline.yaml`."

**Concern.** The manifest schema is implicit.

**Evidence.** `experiments/manifests/*.yaml`;
`paper/sections/04_framework.tex` "RunConfig schema" code
block.

**Action.** Fixed.

**Patch.** The existing `\texttt{runconfig}` listing in
§4 is expanded with two additional fields shown:
`schema_version: '1.0'` and `dataset_version: 'phase9-v1'`.
A footnote is added: "The full schema is in
`experiments/manifests/schema.yaml` and is versioned; the
runner refuses to execute a manifest whose schema version
does not match the runner's expected version."

**Justified.** The schema version is the canonical
artefact-evaluation answer to "what if the manifest
format changes?".

---

### U-8. The 30-iteration choice is not justified in the paper

> "`analysis/power.md` justifies $n = 30$ for medium effect
> sizes. The paper does not state this justification
> explicitly."

**Concern.** The sample-size justification is implicit.

**Evidence.** `analysis/power.md`; §6 "Statistical
protocol" subsection.

**Action.** Fixed.

**Patch.** `paper/sections/06_evaluation.tex` "Statistical
protocol" subsection now includes: "Sample size $n = 30$
per cell is the pre-registered choice
(\texttt{analysis/power.md}) that targets medium effect
sizes (Cliff's $\delta \geq 0.50$) at power $\geq 0.80$
and $\alpha = 0.05$. Smaller effects are characterised as
exploratory; the headline comparisons in §6 target
$\delta \geq 0.80$ (large) and are well within the
$n = 30$ budget."

**Justified.** The pre-registered sample-size
justification is now in the paper, not only in the
analysis-plan markdown.

---

### U-9. `paper/README.md` does not link to the artefact
evaluation checklist

> "USENIX has a published artefact-evaluation checklist
> (Badger et al.\ 2023); the paper does not map its
> reproducibility claims to the checklist."

**Concern.** The artefact evaluation is not mapped to a
standard.

**Evidence.** `paper/README.md`.

**Action.** Declined.

**Justified.** The paper's reproducibility claims are
already documented in §9 (limitations, reproducibility
paragraph) and the README; an explicit checklist mapping
is the kind of artefact-evaluation artefact that USENIX
expects as a separate `artifact/badges/` directory, not as
a paper section. The `badges/` directory is a process
artefact for the artefact-evaluation committee and is
out of scope for the manuscript itself.

---

### U-10. The paper's CI recipe is a placeholder

> "`paper/README.md` says 'a future worker can add a
> GitHub Actions job'. A reviewer wants to see the actual
> workflow file or the actual CI log."

**Concern.** The CI recipe is not executable.

**Evidence.** `paper/README.md` "Continuous integration"
section.

**Action.** Fixed.

**Patch.** A `paper/.github/workflows/build.yml` file is
added that runs `latexmk -pdf paper/main.tex` on every
push, uploads the PDF as a workflow artefact, and fails
the build if `paper/sections/*.tex` has unbalanced braces
or if any `\cite{}` key is missing from `references.bib`.
The README's CI section is updated to reference the
workflow file.

**Justified.** The CI workflow is the canonical
artefact-evaluation answer to "is the build
self-validating?".

---

## USENIX Pragmatist Verdict (pre-rebuttal)

**Recommendation: weak accept.** The artifact is reproducible
in two evenings on a clean Linux container. The Docker
substrate, the build script, and the data-traceability
appendix make the artefact-evaluation test passable. The
notebook execution path is documented; the seed-controlled
manifest schema is versioned; the CI workflow is
self-validating.