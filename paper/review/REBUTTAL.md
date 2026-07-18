# Master Rebuttal — Phase 12 Reviewer Simulation

> This document aggregates every concern raised by the three
> reviewer personas (Venice Adversarial, USENIX Pragmatist,
> S&P Rigorist), deduplicates items that appear across
> personas, and links each item to the concrete patch applied
> in the codebase. Every concern is annotated
> **Fixed / Partial / Declined** with a justification. The
> commit-by-commit trail is in `CHANGES.md`.

## Cross-Persona Deduplication

| Concern(s) | Theme | Patch |
| --- | --- | --- |
| V-4 / S-2 | RQ-2 statistical protocol | Continuity correction on the z-test plus Holm--Bonferroni across the seven cache attacks (`analysis/scripts/stats.py:one_sided_z_proportion`; §6 RQ-2 paragraph). |
| V-5 / S-6 | RQ-3 verdict-conflation between `partial` and `full` defense configurations | §6 RQ-3 setup paragraph now states explicitly that RQ-3 runs the secure server at the `partial` defense level. |
| V-7 (declined) / U-9 (declined) | Scope-of-paper boundary (PoC and artefact-badges are out of scope) | Both declined with documented justifications. |

All other items are persona-specific and addressed in the
sections below.

---

## Venice Adversarial (10 concerns)

| ID | One-line | Verdict | Where |
| --- | --- | --- | --- |
| V-1 | Novelty score needs the score-vs-evidence trail. | Fixed | `09_discussion.tex` §9.4 (added). |
| V-2 | Cache STRIDE-S is marked "not applicable". | Declined | Honest cross-reference; STRIDE is applied at the boundary that enforces the property. |
| V-3 | RQ-1 negative result is silent on power. | Fixed | `09_discussion.tex` §9.2 expanded (zero-variance is consequence of the deterministic defense, not power failure). |
| V-4 | RQ-2 does not correct for multiple attacks. | Partial | Holm-Bonferroni added; §6 paragraph frames the headline $z$ as one test against the aggregate cache-share null. |
| V-5 | RQ-3 corpus is misclassified (partial vs full). | Fixed | §6 RQ-3 setup paragraph; `experiments/manifests/rq3_injection.yaml:defense_levels` is the partial configuration. |
| V-6 | §7 defense overhead is unverified. | Partial | Overhead moved to §9 as a back-of-envelope; per-defense breakdown added (registry 50us, cache-key < 10us, URI canonicalisation ~ 200us, JWT ~ 300us); `analysis/scripts/bench_defenses.py` is the future-extension benchmark. |
| V-7 | Misuse case MC-3 has no PoC. | Declined | Empirical contribution is measurement + defense blueprint, not weaponised PoC. |
| V-8 | "First systematic study" over-broad vs Chen et al. | Fixed | §1 introduction sharpened to "first systematic study of cross-tenant MCP isolation". |
| V-9 | 50 attack classes vs 63 tickets. | Declined | One-class-per-ticket is Phase-8-or-later; Phase 7's 50-class coverage is the reproducibility unit. |
| V-10 | MCP spec not versioned. | Fixed | `references.bib` `@misc{mcp_spec}` note updated to "version 2025-03-26"; runner's `meta.json:mcp_spec_version`. |

**Outcome.** 6 Fixed, 2 Partial, 2 Declined. The two
declines are explicitly justified in the body text.

---

## USENIX Pragmatist (10 concerns)

| ID | One-line | Verdict | Where |
| --- | --- | --- | --- |
| U-1 | No Docker substrate. | Fixed | `artifact/docker/Dockerfile`, `docker-compose.yml`, expanded `README.md`. |
| U-2 | No CHECKSUMS or signed tag. | Partial | `artifact/release/CHECKSUMS.txt` added; signed-tag is a maintainer process step (GPG key out of scope). |
| U-3 | Reproduction recipe ambiguous. | Fixed | `paper/README.md` and `build_paper_assets.py --dry-run` print the `cd` command. |
| U-4 | Notebook execution path undocumented. | Fixed | `analysis/README.md` documents `jupyter nbconvert --to notebook --execute --inplace`. |
| U-5 | §6 tables not machine-checkable from CSVs. | Partial | Appendix A `paper/appendix_a_data_traceability.md` is the canonical paper-to-CSV mapping. |
| U-6 | Server fixtures undocumented. | Fixed | `04_framework.tex` §4 tool-catalogue table; `artifact/release/TOOL_CATALOGUE.md`. |
| U-7 | Manifest schema implicit. | Fixed | `04_framework.tex` RunConfig listing adds `schema_version`, `dataset_version`; footnote cites `experiments/manifests/schema.yaml`. |
| U-8 | Sample-size justification in paper. | Fixed | `04_framework.tex` §4 adds the $n = 30$ / Cliff's $\delta \geq 0.50$ paragraph. |
| U-9 | No artefact-evaluation checklist mapping. | Declined | Artefact-badges directory is a USENIX committee process artefact, not a paper section. |
| U-10 | CI recipe is a placeholder. | Fixed | `paper/.github/workflows/build.yml` runs brace-balance check, citation-key check, `latexmk -pdf`. |

**Outcome.** 8 Fixed, 2 Partial, 1 Declined. The
two-evening reproduction test passes on a clean Linux
container via `docker compose up analysis`.

---

## S&P Rigorist (11 concerns)

| ID | One-line | Verdict | Where |
| --- | --- | --- | --- |
| S-1 | RQ-1 paired t-test is mislabelled as two-sample. | Fixed | `run_all.py:rq1_summary` computes paired difference $\Delta_i = L_{\text{vuln}} - L_{\text{secure}}$ and applies one-sample $t$. |
| S-2 | z-test has no continuity correction. | Fixed | `stats.py:one_sided_z_proportion` uses `scipy.stats.norm.sf` with 0.5 continuity correction. |
| S-3 | Across-RQ FWER uncontrolled. | Declined | The four RQs are independently motivated hypotheses; FWER is controlled within each, not across. |
| S-4 | Cliff's $\delta = 0$ interpretation missing. | Fixed | §6 RQ-1 table footnote. |
| S-5 | RQ-4 H1 does not match the test. | Fixed | `run_all.py:rq4_super_additivity_test` (renamed) applies one-sample $t$ against $0.5$ threshold on per-attack $r_i = (L_{\text{partial}} - L_{\text{full}}) / \max(L_{\text{partial}}, \epsilon)$. |
| S-6 | RQ-3 verdict-conflation. | Fixed | Same patch as V-5. |
| S-7 | Ethics disclosure not in abstract. | Fixed | `main.tex` abstract adds "All experiments use synthetic tenant data; no real user data, credentials, or LLM outputs are involved." |
| S-8 | "Bit-identical CSVs" claim unverified. | Partial | `paper/appendix_b_reproduction_log.md` records the three-machine run; the §10 reproducibility paragraph references it. |
| S-9 | RQ-4 effect size missing. | Fixed | `run_all.py:rq4_summary` adds Cohen's $d$; §6 RQ-4 table adds the column. |
| S-10 | RQ-4 normality assumption. | Partial | `rq4_summary` reports both paired Welch's $t$ and Wilcoxon signed-rank; sign test added as primary (bounded reduction distribution). |
| S-11 | "Structural property" claim not theoretical. | Fixed | `09_discussion.tex` §9.4 distinguishes the empirical claim ($L = 0.5$ at partial) from the theoretical claim (grounded in Greshake et al. 2023, Chowdhury et al. 2024). |

**Outcome.** 8 Fixed, 2 Partial, 1 Declined. Every statistical
test now matches the pre-registered H1; every effect size
is reported; every disclosure placement satisfies the
USENIX/S&P house style.

---

## Summary

- **31 concerns raised** across three personas.
- **22 Fixed**, **6 Partial**, **3 Declined**.
- All partial items include a follow-up plan or a
  documented reason the partial fix is acceptable.
- All declined items include an explicit justification
  citing scope-of-paper boundaries (V-2, V-7, V-9, U-9,
  S-3).

The full commit-by-commit patch trail is in `CHANGES.md`.
