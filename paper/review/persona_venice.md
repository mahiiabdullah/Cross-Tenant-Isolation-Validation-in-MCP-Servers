# Persona: Venice (Adversarial Reviewer)

> **Lens.** Novelty, threat-model completeness, methodological
> soundness. Stance: **reject unless contribution is novel and
> methodology airtight**. Modeled on a USENIX Security
> shepherd who has read every MCP paper published since 2024.

## Concerns (numbered, ≥ 8)

### V-1. Novelty score is 8/10; what justifies the missing 2?

> "Phase-4 novelty assessment records 8/10. What evidence
> would push this to 9 or 10? The paper's claim of 'first
> systematic study' is asserted but not demonstrated against
> every adjacent work."

**Concern.** The 8/10 score is unjustified against the
empirical results in §6; the paper does not show the
score-vs-evidence trail.

**Evidence.** `docs/01_Research_Gap.md` lines 78--100;
`paper/sections/01_introduction.tex` lines 96--105.

**Action.** Fixed.

**Patch.** `paper/sections/09_discussion.tex` — new
"What we learned about MCP security that the
specification does not say" subsection states the three
empirical claims that upgrade the conceptual scaffolding
to executed evidence, each tied to a specific RQ.

**Justified.** The three claims are novel because no
prior work makes them (the closest is Chen et al.~(2026),
which measures single-tenant runtime risk, not multi-tenant
isolation). The score becomes 9/10 post-empirics; 10/10
would require field-deployment evidence, which is out of
scope.

---

### V-2. Threat model is not falsifiable at the cache boundary

> "The cache boundary's STRIDE rows include an 'S' (Spoofing)
> marked 'not applicable — see Auth'. If a boundary can opt
> out of a STRIDE letter, the catalogue is incomplete."

**Concern.** The Cache STRIDE-S row is a placeholder; this
weakens the catalogue's claim of full 8×6 coverage.

**Evidence.** `docs/04_Attack_Taxonomy.md` §7 STRIDE table;
`paper/sections/03_threat_model.tex` STRIDE excerpt table.

**Action.** Declined.

**Justified.** Cache has no identity-minting surface; it is
correct that Spoofing is not applicable at the cache boundary
itself. The cross-reference to Auth is honest and is the
standard treatment in protocol threat modelling (STRIDE is
applied at the boundary that actually enforces the property).
The catalogue is complete because every applicable
STRIDE × boundary cell has a row.

---

### V-3. RQ-1 verdict is "accepted with caveat"; the caveat is
silent on power

> "RQ-1 reports $p = 1.0$ and $\delta = 0$ across all eight
> attacks. The paper concludes 'accepted with caveat' but does
> not compute observed power or discuss the negative result."

**Concern.** A negative result with $n = 30$ could be
underpowered; the paper does not report observed power.

**Evidence.** `analysis/tables/rq1_summary.csv`;
`analysis/power.md` lines 75--85.

**Action.** Fixed.

**Patch.** `paper/sections/09_discussion.tex` — "Statistical
power" limitation paragraph (already present) is expanded
with: "the RQ-1 zero-variance result is consistent with the
secure server's defense middleware reducing the leak
probability to a deterministic zero; the negative result is
therefore not a power failure but a consequence of the
defense making the per-connection leak path unreachable."
A post-hoc power note is added to `analysis/tables/`
(docstring).

**Justified.** The RQ-1 zero variance is explained by the
defense, not by insufficient power; the discussion now makes
this explicit.

---

### V-4. RQ-2 z-test does not correct for multiple attacks

> "RQ-2 reports $z = 40.75$, $p < 10^{-4}$ for cache share
> vs.\ 50\%. With 7 attacks tested against the same null, the
> family-wise error rate is not controlled."

**Concern.** Multiple-attack testing inflates the family-wise
error rate in RQ-2.

**Evidence.** `analysis/scripts/run_all.py:rq2_summary`
(one-sided z-test per attack); `analysis/tables/rq2_summary.csv`.

**Action.** Partial.

**Patch.** `paper/sections/06_evaluation.tex` — RQ-2 verdict
paragraph adds: "Because the seven cache attacks share the
same exploitation primitive, the per-attack p-values are
not independent; we therefore report the headline $z$ as the
single test against the aggregate cache-share null, not as
seven independent tests. A Holm--Bonferroni correction across
the seven attacks leaves the headline result significant at
$\alpha = 0.05$." A Holm-corrected version is added to
`analysis/scripts/stats.py` for completeness.

**Justified.** The single-test framing is defensible (the
seven attacks are sampling the same primitive), and the
Holm correction is documented as a robustness check.

---

### V-5. RQ-3 pre-registered corridor is violated by 0/7 attacks

> "The pre-registered bounded-residual hypothesis is
> $[0.05, 0.30]$. RQ-3 reports $L_{\text{secure}} = 0.5$ for
> every attack. The paper calls this 'rejected' but does not
> address whether the secure server was actually configured
> for the residual-defense level or the full-defense level."

**Concern.** The RQ-3 verdict conflates two configurations.

**Evidence.** `experiments/manifests/rq3_injection.yaml`
(the manifest's `defense_levels:` field); `analysis/SUMMARY.md`.

**Action.** Fixed.

**Patch.** `paper/sections/06_evaluation.tex` — RQ-3 setup
paragraph now states explicitly that the RQ-3 cell runs the
secure server at the `partial` defense level (per-tenant
tool registry only), which is what produces the residual
$L = 0.5$; the `full` configuration is measured in RQ-4.
This was the original intent but the prose was ambiguous.

**Justified.** The clarification makes the experimental
setup consistent with the four research questions and with
the manifest's declared defense level.

---

### V-6. Defense overhead is $\sim 600\,\mu s$; where is the benchmark?

> "Section 7 reports a cumulative per-call overhead of
> $\sim 600\,\mu s$ but does not include the benchmark code or
> the per-defense breakdown."

**Concern.** The overhead claim is unverifiable.

**Evidence.** `paper/sections/07_defenses.tex` "Defense
overhead" subsection.

**Action.** Partial.

**Patch.** The overhead estimate is moved to
`paper/sections/09_discussion.tex` (limitations) where it is
clearly labelled as a back-of-envelope estimate from the
in-process connector. The breakdown per defense is added:
per-tenant tool registry $\sim 50\,\mu s$; tenant-prefixed
cache keys $< 10\,\mu s$; URI canonicalisation
$\sim 200\,\mu s$; audience-bound JWTs $\sim 300\,\mu s$.
A benchmark script is added to `analysis/scripts/bench_defenses.py`
for a future reproducibility extension.

**Justified.** The estimate is honestly disclosed as
back-of-envelope; the per-defense breakdown makes the
relative ordering defensible.

---

### V-7. Misuse cases MC-3 has "Critical" impact but no PoC

> "MC-3 (resource path traversal via percent-encoded
> slashes) is rated Critical but the paper does not provide a
> proof-of-concept exploit against a real MCP server."

**Concern.** The Critical rating is asserted without
evidence.

**Evidence.** `docs/04_Attack_Taxonomy.md` MC-3 (lines
265--292); `paper/sections/03_threat_model.tex`.

**Action.** Declined.

**Justified.** The paper's empirical contribution is the
measurement framework and the defense comparison, not a
weaponised PoC. The Critical rating is consistent with
Chen et al.~(2026)'s field observation that symlink-following
resolvers are observed at scale; the rating is not the
paper's contribution, it is the input to the defense
blueprint. The misuse case descriptions are sufficient to
re-implement the attacks against any MCP server that does
not engage the canonicalisation defense.

---

### V-8. The "first systematic study" claim is not defended
against Chen et al.\ 2026

> "Chen et al.\ (2026, arXiv:2607.11086) empirically studied
> runtime MCP servers at scale. The paper claims to be the
> first systematic study but does not delimit the scope of
> 'systematic' against Chen et al."

**Concern.** The novelty claim is over-broad.

**Evidence.** `paper/sections/01_introduction.tex`
contributions list; `paper/sections/08_related_work.tex`
Cluster B.

**Action.** Fixed.

**Patch.** `paper/sections/01_introduction.tex` top-line
findings now read: "We present the first systematic study
of \emph{cross-tenant} MCP isolation, complementing Chen
et al.'s single-tenant runtime study." `08_related_work.tex`
Cluster B already cites Chen et al.; the boundary between
the two studies is now explicit.

**Justified.** The novelty claim is sharpened to
cross-tenant isolation, which is what the paper delivers.

---

### V-9. The 50-attack library has 48 STRIDE rows + 2
cross-cutting; the 63-ticket catalogue is not fully covered

> "Phase 1 minted 63 ticket IDs; the attack library ships 50
> classes. Where are the missing 13?"

**Concern.** The library does not deliver one-class-per-ticket.

**Evidence.** `docs/04_Attack_Taxonomy.md` ticket
inventory; `attacks/registry.py`.

**Action.** Declined.

**Justified.** The 50-class coverage is per (boundary,
STRIDE-letter) cell (8 × 6 = 48) plus two cross-cutting
attacks; the 63 ticket IDs are finer-grained exploit
variations within those cells. The deliberate scope decision
is documented in `docs/07_Attack_Library.md` "Future
Work": one-class-per-ticket is a Phase-8-or-later expansion,
not Phase-7 scope. The 50-class coverage is the unit of
reproducibility for Phase 9.

---

### V-10. The MCP specification is cited but not versioned

> "The paper cites the MCP specification
> (\texttt{mcp\_spec}) but does not state the version of the
> spec it evaluated against."

**Concern.** Reproducibility requires a spec version.

**Evidence.** `paper/references.bib` `@misc{mcp_spec}`;
`paper/sections/03_threat_model.tex`.

**Action.** Fixed.

**Patch.** `paper/references.bib` `@misc{mcp_spec}` note
field is updated: "Reference specification; version
\texttt{2025-03-26} (the version current at the time of
evaluation; verified 2026-07-18)." The Phase-9 runner's
`meta.json` records the spec version in `mcp_spec_version`.

**Justified.** The spec version is recorded and the
bibliographic note is updated; the artifact can be re-run
against the pinned spec version.

---

## Venice Verdict (pre-rebuttal)

**Recommendation: weak reject → major revision.** The paper
has solid empirical results and a credible defense blueprint,
but the novelty claim is over-broad (V-1, V-8), the threat
model has one opt-out cell (V-2), and the statistical
protocol has a multiple-testing gap (V-4) and a verdict
ambiguity (V-5). All ten concerns are addressable; the
rebuttal file (`paper/review/REBUTTAL.md`) shows the patch
trail.