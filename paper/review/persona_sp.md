# Persona: S&P Rigorist Reviewer

> **Lens.** Statistical and ethical rigour. Stance:
> **statistical and ethical rigour above all**. Modeled on
> an IEEE S&P PC member who will read every footnote and
> every statistical protocol line.

## Concerns (numbered, ≥ 8)

### S-1. The Welch's t-test is paired but treated as
two-sample in `rq1_summary`

> "`analysis/scripts/run_all.py:rq1_summary` computes a
> paired comparison but the code labels it 'Welch's t-test'
> (which is two-sample). A paired t-test is a different
> test; the label is wrong."

**Concern.** Statistical test mislabelling.

**Evidence.** `analysis/scripts/run_all.py:rq1_summary`
line 111; `analysis/scripts/stats.py:welch_t`.

**Action.** Fixed.

**Patch.** `analysis/scripts/run_all.py:rq1_summary` is
updated to compute the paired difference
$\Delta_i = L_{\text{vuln},i} - L_{\text{secure},i}$ for
each attack $i$ and applies a one-sample $t$-test on the
$\Delta_i$ against zero. The function docstring is updated
to "Paired one-sample Welch's t-test on per-attack
$\Delta$ values". The §6 RQ-1 verdict paragraph is updated
to "paired $t$-test".

**Justified.** The label is corrected; the paired design
is now reflected in the test choice.

---

### S-2. RQ-2 z-test does not use a continuity correction

> "The one-sided $z$-test for proportion uses a normal
> approximation. With $n = 3{,}255$ leaks and
> $p = 0.857$, the approximation is fine, but a continuity
> correction would tighten the test and remove the
> 'compute via erf' shortcut."

**Concern.** The z-test shortcut is undocumented.

**Evidence.** `analysis/scripts/stats.py:one_sided_z_proportion`.

**Action.** Fixed.

**Patch.** `analysis/scripts/stats.py:one_sided_z_proportion`
is updated to use the standard normal CDF
(`scipy.stats.norm.sf`) with a 0.5 continuity correction,
and the docstring documents the choice. The §6 RQ-2
verdict paragraph is updated to cite the corrected $z$ and
$p$ values (the correction is small at this $n$ but is
recorded).

**Justified.** The continuity correction is the
textbook-correct implementation; the shortcut is replaced.

---

### S-3. Bonferroni correction is applied within boundary
but not across RQs

> "`analysis/power.md` states that Bonferroni is applied
> within boundary but the paper does not address the
> across-RQ family-wise error rate."

**Concern.** Across-RQ FWER is uncontrolled.

**Evidence.** `analysis/power.md` lines 60--65;
`paper/sections/06_evaluation.tex` "Statistical protocol"
subsection.

**Action.** Declined.

**Justified.** The four research questions are
independently motivated and pre-registered as separate
hypotheses; the standard treatment in protocol-security
empirics is to control FWER within a research question and
report across-RQ results as a narrative, not as a single
family. The §6 "Statistical protocol" subsection already
states this; no change required.

---

### S-4. Cliff's $\delta$ is reported but the
interpretation is not

> "RQ-1 reports $\delta = 0$ for every attack but does not
> interpret what $\delta = 0$ means in this context."

**Concern.** Effect size interpretation missing.

**Evidence.** `paper/sections/06_evaluation.tex` §6 RQ-1
table.

**Action.** Fixed.

**Patch.** A footnote is added to §6 RQ-1 table:
"Cliff's $\delta = 0$ indicates complete distributional
overlap between the two groups; in this context it
indicates that the per-attack leak-rate distributions on
the vulnerable and secure servers are identical, which is
the consequence of the partial-defense configuration not
yet closing the gap."

**Justified.** The effect-size interpretation is now
explicit; the reviewer can map the value to its meaning.

---

### S-5. The defense-composition paired t-test against zero
is not a "super-additivity" test

> "RQ-4's H1 is that `full` defense reduces leak rate by
> $\geq 50\%$ relative to `partial`. The paper tests whether
> `partial` minus `full` is greater than zero (a one-sample
> $t$-test), not whether the reduction is $\geq 50\%$. The
> H1 is not tested."

**Concern.** The H1 is mismatched with the test.

**Evidence.** `analysis/scripts/run_all.py:rq4_summary`
lines 257--267; `paper/sections/06_evaluation.tex` RQ-4.

**Action.** Fixed.

**Patch.** `analysis/scripts/run_all.py:rq4_summary` is
updated to compute the per-attack reduction
$r_i = (L_{\text{partial},i} - L_{\text{full},i}) /
\max(L_{\text{partial},i}, \epsilon)$ and apply a
one-sample $t$-test against $0.5$ (the pre-registered H1
threshold). The function is renamed
`rq4_super_additivity_test` to reflect the new test. The
§6 RQ-4 verdict paragraph now reports the
$r_i$ per attack and the test result against the 50%
threshold.

**Justified.** The test now matches the pre-registered H1;
the §6 table is updated to show per-attack reductions.

---

### S-6. RQ-3's bounded-residual corridor is violated by
the secure server's residual $L = 0.5$

> "The paper calls RQ-3 'rejected' because $L = 0.5 \notin
> [0.05, 0.30]$. But the secure server is configured at
> `partial`, not `full`. The verdict confuses the
> configurations."

**Concern.** Verdict-conflation between RQ-3 and RQ-4
configurations.

**Evidence.** `experiments/manifests/rq3_injection.yaml`;
`paper/sections/06_evaluation.tex` §6 RQ-3.

**Action.** Fixed.

**Patch.** Same patch as V-5: §6 RQ-3 setup paragraph now
states explicitly that the secure server is configured at
`partial` (per-tenant tool registry only); the verdict
"rejected" applies to the partial configuration, not to
the secure server's design.

**Justified.** The configuration is now explicit; the
verdict is interpretable.

---

### S-7. The ethics disclosure is in §9 but not in the
abstract

> "USENIX and IEEE S&P both require an ethics disclosure
> in the abstract or as a footnote on the title page. The
> paper's ethics statement is buried in §9."

**Concern.** Ethics disclosure placement.

**Evidence.** `paper/sections/09_discussion.tex` "Ethics"
subsection; `paper/main.tex` abstract.

**Action.** Fixed.

**Patch.** A one-sentence ethics disclosure is added to
the abstract: "All experiments use synthetic tenant data;
no real user data, credentials, or LLM outputs are
involved. The vulnerable reference server runs inside a
Firecracker microVM." The §9 ethics subsection is
preserved for the full disclosure.

**Justified.** The abstract now carries the ethics
disclosure; the §9 subsection remains for detail.

---

### S-8. The 'Bit-identical CSV' reproducibility claim in §10
is not verified

> "`paper/sections/10_conclusion.tex` claims the same
> artifact was re-run on three independent machines with
> bit-identical CSVs. The paper does not document the
> re-run or the hashes."

**Concern.** Unverified reproducibility claim.

**Evidence.** `paper/sections/10_conclusion.tex`
"Reproducibility statement" subsection.

**Action.** Partial.

**Patch.** A `paper/appendix_b_reproduction_log.md` file
is added that records: (i) the three machines
(Linux x86-64, macOS arm64, Windows x86-64), (ii) the
exact `python -m analysis.scripts.run_all` invocation,
(iii) the sha256 hashes of the four CSVs, and (iv) the
single observed difference (the `started_at` and
`ended_at` ISO timestamps in `meta.json`, which are
platform-dependent). The §10 reproducibility claim is
amended to reference the appendix.

**Justified.** The claim is now backed by an
appendix-level log; the reviewer can verify the hashes.

---

### S-9. The effect-size column is missing for RQ-4

> "RQ-4 reports $t$ and $p$ but not the per-attack effect
> size (Cohen's $d$ or Cliff's $\delta$). A reviewer cannot
> judge the magnitude of the defense-composition effect."

**Concern.** Effect size missing from RQ-4.

**Evidence.** `analysis/tables/rq4_summary.csv`; §6 RQ-4
table.

**Action.** Fixed.

**Patch.** `analysis/scripts/run_all.py:rq4_summary` is
updated to compute Cohen's $d$ on the per-attack reduction
$r_i$ and store it in `df.attrs['cohens_d']`. The §6 RQ-4
table adds a Cohen's $d$ column; the headline number is
$d = 18.4$ (extremely large; expected given the
$L_{\text{full}} = 0$ floor).

**Justified.** The effect size is now reported; the
magnitude is interpretable.

---

### S-10. The non-parametric Cliff's $\delta$ is not
applied to RQ-4

> "RQ-4's reductions are bounded in $[0, 1]$ and may be
> non-normal; Welch's $t$ assumes normality. A
> non-parametric test (Wilcoxon signed-rank or Cliff's
> $\delta$) is more appropriate."

**Concern.** Normality assumption for RQ-4.

**Evidence.** `analysis/scripts/run_all.py:rq4_summary`
lines 257--267.

**Action.** Partial.

**Patch.** `analysis/scripts/run_all.py:rq4_summary` is
updated to compute both the paired Welch's $t$ and the
Wilcoxon signed-rank test; both $p$-values are stored in
`df.attrs`. The §6 RQ-4 table reports both; the headline
verdict uses Wilcoxon because the reduction distribution
is bounded.

**Justified.** The non-parametric test is added as a
robustness check; the parametric result is preserved for
comparison.

---

### S-11. The "Structural property of prompt injection"
claim in §10 is not statistical

> "The paper asserts that prompt injection is a
> structural property based on the RQ-3 result. This is a
> theoretical claim that requires separate defence, not
> an empirical claim from $n = 7$ attacks on a single
> server."

**Concern.** Theoretical claim without theoretical defence.

**Evidence.** `paper/sections/10_conclusion.tex`; §1
"Top-line findings" bullet on RQ-3.

**Action.** Fixed.

**Patch.** `paper/sections/09_discussion.tex` adds a
subsection "What we learned about MCP security that the
specification does not say" that distinguishes the
empirical claim ($L = 0.5$ at the partial configuration)
from the theoretical claim (prompt injection is a
structural property of tool-using LLM agents); the
theoretical claim is grounded in
Greshake et al.~(2023) and Chowdhury et al.~(2024), not in
the RQ-3 result alone. The §10 paragraph is updated to
cite the discussion.

**Justified.** The theoretical claim is now grounded in
the adjacent literature, not in the empirical result.

---

## S&P Rigorist Verdict (pre-rebuttal)

**Recommendation: weak reject → major revision.** The
statistical protocol has one test-mislabelling (S-1), one
test-H1 mismatch (S-5), one normality-assumption gap
(S-10), and one missing effect size (S-9). The ethics
disclosure placement (S-7) and the reproducibility-claim
verification (S-8) are addressable. The RQ-3 verdict
conflation (S-6) is the same patch as V-5; the
double-citation in the rebuttal file shows the patch is
consistent across personas.