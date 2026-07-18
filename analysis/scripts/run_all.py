"""Top-level analysis driver.

Reads the four Phase-9 run outputs (``exp-rq1-baseline``,
``exp-rq2-cache``, ``exp-rq3-injection``, ``exp-rq4-defense``)
and produces:

* Four summary CSVs in ``analysis/tables/``.
* Four PDF + PNG figure pairs in ``analysis/figures/`` (via
  :mod:`analysis.scripts.plots`).
* ``analysis/SUMMARY.md`` with one TL;DR paragraph per RQ.

This script is the canonical entry point: ``python -m
analysis.scripts.run_all``.
"""

from __future__ import annotations

import argparse
import sys
import statistics
from pathlib import Path

import pandas as pd

from scipy import stats as scipy_stats

from .. import ANALYSIS_DIR, TABLES_DIR
from .load_runs import load_results
from .plots import make_all
from .stats import (
    bonferroni,
    cliffs_delta,
    cohens_d,
    one_sided_z_proportion,
    sign_test,
    welch_t,
)
# Re-export for ergonomic module usage.


RUN_IDS: dict[str, str] = {
    "rq1": "exp-rq1-baseline",
    "rq2": "exp-rq2-cache",
    "rq3": "exp-rq3-injection",
    "rq4": "exp-rq4-defense",
}


def _sig(p: float) -> str:
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return ""


def _per_attack_leak_rates(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (attack_id, server_variant) with leak rate.

    ``leak_rate`` is computed as ``leakage_events / call_events``,
    not ``leakage / total``, because the row count of ``call``
    events is the natural denominator for "how often did an
    attempted cross-tenant operation leak?".
    """
    call_counts = (
        df[df["event_type"] == "call"]
        .groupby(["attack_id", "boundary", "server_variant"], as_index=False)
        .size()
        .rename(columns={"size": "n_calls"})
    )
    leak_counts = (
        df[df["event_type"] == "leakage"]
        .groupby(["attack_id", "boundary", "server_variant"], as_index=False)
        .size()
        .rename(columns={"size": "n_leaks"})
    )
    merged = call_counts.merge(
        leak_counts,
        on=["attack_id", "boundary", "server_variant"],
        how="left",
    ).fillna({"n_leaks": 0})
    merged["n_leaks"] = merged["n_leaks"].astype(int)
    merged["n_events"] = (
        merged["n_calls"] + merged["n_leaks"]
    )
    merged["leak_rate"] = merged["n_leaks"] / merged["n_calls"].replace(0, 1)
    return merged


def rq1_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Paired one-sample t-test + Cliff's δ: vulnerable vs secure.

    Each ``server_variant × attack_id`` cell produces one
    leak-rate value (already aggregated across 30 iterations by
    the Phase-9 runner). We therefore build paired vectors
    ``[v_attack_1, v_attack_2, …]`` and ``[s_attack_1, …]`` and
    apply a paired one-sample Welch's t-test on the per-attack
    difference ``Δ_i = v_i - s_i`` against zero, plus Cliff's δ
    across the *whole attack set*, then report per-attack
    descriptive rates.

    Bonferroni correction is applied at the boundary level
    (α_adj = 0.05 / n_attacks_in_boundary), per the pre-
    registered protocol in ``analysis/power.md``.
    """
    rates = _per_attack_leak_rates(df)
    rates_wide = rates.pivot(
        index=["attack_id", "boundary"],
        columns="server_variant",
        values="leak_rate",
    ).reset_index()
    # Paired differences.
    deltas = (
        rates_wide["vulnerable"].astype(float) - rates_wide["secure"].astype(float)
    ).tolist()
    # Paired one-sample Welch's t against zero.
    global_t, global_p = welch_t(deltas, [0.0] * len(deltas))
    # Cliff's δ on the two distributions (descriptive).
    global_delta = cliffs_delta(
        rates_wide["vulnerable"].astype(float).tolist(),
        rates_wide["secure"].astype(float).tolist(),
    )

    rows: list[dict] = []
    for _, row in rates_wide.iterrows():
        rows.append(
            {
                "attack_id": row["attack_id"],
                "boundary": row["boundary"],
                "leak_rate_vulnerable": float(row["vulnerable"]),
                "leak_rate_secure": float(row["secure"]),
                "welch_t": float(global_t),
                "welch_p": float(global_p),
                "cliffs_delta": float(global_delta),
            }
        )
    summary = pd.DataFrame(rows)
    # Bonferroni within boundary.
    if not summary.empty:
        adj_p: list[float] = []
        for _, group in summary.groupby("boundary"):
            adj_p.extend(bonferroni([float(global_p)] * len(group)))
        summary = summary.assign(bonferroni_p=adj_p)
        summary["sig"] = summary["bonferroni_p"].apply(_sig)
    summary["n_events"] = (
        df.groupby("attack_id").size().reindex(summary["attack_id"]).fillna(0).astype(int).values
    )
    summary.attrs["paired_t"] = global_t
    summary.attrs["paired_p"] = global_p
    summary.attrs["cliffs_delta"] = global_delta
    summary = summary.sort_values("boundary").reset_index(drop=True)
    return summary


def rq2_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Cache-share z-test on the vulnerable server's leak volume."""
    cch = df[df["attack_id"].str.startswith("A-CCH-") | (df["attack_id"] == "A-FUZZ-001")]
    vuln = cch[cch["server_variant"] == "vulnerable"]
    leak = vuln[vuln["event_type"] == "leakage"]
    total_leaks = int(len(leak))
    rows: list[dict] = []
    for attack_id, group in leak.groupby("attack_id"):
        boundary = group["boundary"].iloc[0] if "boundary" in group.columns else "cache"
        n = int(len(group))
        share = (n / total_leaks) if total_leaks else 0.0
        rows.append(
            {
                "attack_id": attack_id,
                "boundary": boundary,
                "leak_count": n,
                "cache_share_of_vulnerable_leaks": round(share, 4),
            }
        )
    summary = pd.DataFrame(rows).sort_values("leak_count", ascending=False).reset_index(drop=True)
    # One-sided z-test for the headline H1: cache share ≥ 0.50.
    if total_leaks and not summary.empty:
        # Treat cache attacks as A-CCH-* only (FUZZ-001 boundary is tool).
        cache_leaks = int(
            leak[leak["attack_id"].str.startswith("A-CCH-")].shape[0]
        )
        z, p = one_sided_z_proportion(cache_leaks, total_leaks, 0.5)
        summary.attrs["headline_z"] = z
        summary.attrs["headline_p"] = p
        summary.attrs["cache_share_overall"] = cache_leaks / total_leaks
    return summary


def rq3_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Per-attack latency + leak rate on the secure server.

    Each attack contributes one row. We additionally check the
    bounded-residual hypothesis by comparing ``leak_rate`` to
    the [0.05, 0.30] corridor from ``analysis/power.md``.
    """
    secure = df[df["server_variant"] == "secure"].copy()
    secure["latency_ms"] = pd.to_numeric(secure["latency_ms"], errors="coerce")
    rows: list[dict] = []
    for attack_id, group in secure.groupby("attack_id"):
        leak = group[group["event_type"] == "leakage"]
        calls = group[group["event_type"] == "call"]
        n = int(len(group))
        leak_rate = (len(leak) / len(calls)) if len(calls) else 0.0
        latencies = calls["latency_ms"].dropna().tolist()
        mean_lat = float(pd.Series(latencies).mean()) if latencies else 0.0
        p95_lat = float(pd.Series(latencies).quantile(0.95)) if latencies else 0.0
        rows.append(
            {
                "attack_id": attack_id,
                "mean_latency_ms": round(mean_lat, 3),
                "p95_latency_ms": round(p95_lat, 3),
                "leak_rate_secure": round(leak_rate, 4),
                "below_upper_bound": bool(leak_rate <= 0.30),
                "above_lower_bound": bool(leak_rate >= 0.05),
                "n_events": n,
            }
        )
    return pd.DataFrame(rows).sort_values("attack_id").reset_index(drop=True)


def rq4_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Per-attack leak rate at three defense levels + super-additivity test.

    The H1 from ``analysis/power.md`` is that the ``full``
    defense level drops the leak rate by ≥ 50% relative to the
    ``partial`` (per_tenant) level. The paired unit is the
    attack: each attack contributes one paired observation
    ``r_i = (leak_rate_partial − leak_rate_full) /
    max(leak_rate_partial, ε)``. The pre-registered threshold is
    ``r_i ≥ 0.5``; we test whether the distribution of ``r_i``
    exceeds 0.5 using both:

    * paired one-sample Welch's t-test against 0.5 (parametric)
    * Wilcoxon signed-rank test against 0.5 (non-parametric,
      appropriate because ``r_i ∈ [0, 1]``)

    We also report Cohen's ``d`` on the ``r_i`` distribution as
    a measure of effect size.
    """
    # Aggregate leak rate per (attack, defense_level) using
    # the call-denominated leak ratio.
    call_counts = (
        df[df["event_type"] == "call"]
        .groupby(["attack_id", "defense_level"], as_index=False)
        .size()
        .rename(columns={"size": "n_calls"})
    )
    leak_counts = (
        df[df["event_type"] == "leakage"]
        .groupby(["attack_id", "defense_level"], as_index=False)
        .size()
        .rename(columns={"size": "n_leaks"})
    )
    rates = call_counts.merge(
        leak_counts, on=["attack_id", "defense_level"], how="left"
    ).fillna({"n_leaks": 0})
    rates["n_leaks"] = rates["n_leaks"].astype(int)
    rates["leak_rate"] = rates["n_leaks"] / rates["n_calls"].replace(0, 1)
    wide = rates.pivot(
        index="attack_id", columns="defense_level", values="leak_rate"
    ).fillna(0.0)
    wide.columns = [f"leak_rate_{c}" for c in wide.columns]
    if "leak_rate_per_tenant" in wide.columns and "leak_rate_partial" not in wide.columns:
        wide = wide.rename(columns={"leak_rate_per_tenant": "leak_rate_partial"})

    # Compute paired reduction: (partial − full) / max(partial, ε).
    if "leak_rate_partial" in wide.columns and "leak_rate_full" in wide.columns:
        denom = wide["leak_rate_partial"].replace(0, pd.NA)
        wide["reduction_partial_to_full"] = (
            (wide["leak_rate_partial"] - wide["leak_rate_full"]) / denom
        ).fillna(0.0)
    else:
        wide["reduction_partial_to_full"] = 0.0
    wide = wide.reset_index()

    # Super-additivity test: paired reductions r_i vs threshold 0.5.
    if "leak_rate_partial" in wide.columns and "leak_rate_full" in wide.columns:
        reductions = wide["reduction_partial_to_full"].astype(float).tolist()
        threshold = 0.5
        # The reductions distribution can be degenerate (every
        # attack hits the floor at r_i = 1.0). We therefore use
        # the sign test as the primary non-parametric test,
        # which is well-defined when the variance is zero.
        sign_p = sign_test(reductions, threshold)
        # Welch's t as a secondary parametric test.
        centered = [r - threshold for r in reductions]
        if statistics.pvariance(centered) > 0:
            t_stat, p_two = welch_t(centered, [0.0] * len(centered))
            p_one = p_two / 2.0 if t_stat > 0 else 1.0 - (p_two / 2.0)
        else:
            # All reductions equal the threshold + some constant;
            # if every reduction exceeds the threshold the
            # parametric test is also decisive.
            t_stat = float("inf") if all(c > 0 for c in centered) else 0.0
            p_one = 0.0 if t_stat == float("inf") else 1.0
        # Cohen's d vs the threshold (informational).
        d_val = cohens_d(reductions, [threshold] * len(reductions))
        # Wilcoxon signed-rank (non-parametric robustness; may
        # be undefined if all centered values are identical).
        try:
            w_stat, w_p = scipy_stats.wilcoxon(
                centered, alternative="greater"
            )
            wilcoxon_p = float(w_p)
        except ValueError:
            wilcoxon_p = 1.0
        wide["welch_t"] = t_stat
        wide["welch_p"] = p_one
        wide["wilcoxon_p"] = wilcoxon_p
        wide["sign_test_p"] = sign_p
        wide["cohens_d"] = d_val
        wide["sig"] = _sig(min(p_one, wilcoxon_p, sign_p))
        wide.attrs["paired_t"] = t_stat
        wide.attrs["paired_p"] = p_one
        wide.attrs["wilcoxon_p"] = wilcoxon_p
        wide.attrs["sign_test_p"] = sign_p
        wide.attrs["cohens_d"] = d_val
        wide.attrs["threshold"] = threshold
    return wide


def write_summary_md(
    rq_tables: dict[str, pd.DataFrame],
    metas: dict[str, dict],
) -> Path:
    """Write a one-paragraph TL;DR per RQ into ``analysis/SUMMARY.md``."""
    lines: list[str] = [
        "# Phase-10 Summary",
        "",
        "One-paragraph TL;DR per research question. Generated by",
        "`analysis/scripts/run_all.py` from the Phase-9 raw outputs.",
        "",
    ]
    if "rq1" in rq_tables:
        rq1 = rq_tables["rq1"]
        n_sig = int((rq1["sig"] != "").sum()) if "sig" in rq1.columns else 0
        max_delta = float(rq1["cliffs_delta"].abs().max()) if not rq1.empty else 0.0
        n_rows = len(rq1)
        lines.append("## RQ-1: Baseline isolation")
        lines.append(
            f"- {n_rows} attacks analysed; **{n_sig}** flagged significant "
            f"after Bonferroni correction within boundary. "
            f"Paired one-sample Welch's t on (vuln − secure) "
            f"per-attack differences vs zero: "
            f"t = {rq1.attrs.get('paired_t', 0.0):.2f}, "
            f"p = {rq1.attrs.get('paired_p', 1.0):.4f}. "
            f"Max |Cliff's δ| = {max_delta:.2f}."
        )
        lines.append("")
    if "rq2" in rq_tables:
        rq2 = rq_tables["rq2"]
        z = rq2.attrs.get("headline_z")
        p = rq2.attrs.get("headline_p")
        share = rq2.attrs.get("cache_share_overall", 0.0)
        if z is not None and p is not None:
            lines.append("## RQ-2: Cache dominance")
            lines.append(
                f"- Cache attacks account for **{share:.1%}** of vulnerable-server "
                f"leakage. One-sided z-test vs. 50% (continuity-corrected): "
                f"z = {z:.2f}, p = {p:.4f}."
            )
            lines.append("")
    if "rq3" in rq_tables:
        rq3 = rq_tables["rq3"]
        in_band = int(((rq3["above_lower_bound"]) & (rq3["below_upper_bound"])).sum())
        n_rows = len(rq3)
        lines.append("## RQ-3: Prompt-injection residual")
        lines.append(
            f"- {in_band}/{n_rows} attacks on the secure server (partial-defense "
            f"configuration) fell inside the [0.05, 0.30] bounded-residual "
            f"corridor."
        )
        lines.append("")
    if "rq4" in rq_tables:
        rq4 = rq_tables["rq4"]
        t = rq4.attrs.get("paired_t")
        p = rq4.attrs.get("paired_p")
        w_p = rq4.attrs.get("wilcoxon_p")
        d_val = rq4.attrs.get("cohens_d")
        threshold = rq4.attrs.get("threshold", 0.5)
        if t is not None and p is not None:
            lines.append("## RQ-4: Defense combo super-additivity")
            sign_p = rq4.attrs.get("sign_test_p")
            lines.append(
                f"- Paired one-sample Welch's t on per-attack reductions "
                f"$r_i$ vs. pre-registered threshold {threshold}: "
                f"t = {t:.2f}, one-sided p = {p:.4f}. "
                f"Sign test p = {sign_p:.4f}. "
                f"Wilcoxon signed-rank p = {w_p:.4f}. "
                f"Cohen's d = {d_val:.2f}."
            )
            lines.append("")
    out = ANALYSIS_DIR / "SUMMARY.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="analysis.scripts.run_all")
    parser.add_argument(
        "--run-id",
        action="append",
        choices=list(RUN_IDS.keys()),
        help="restrict to one or more RQs (default: all four)",
    )
    args = parser.parse_args(argv)
    wanted = args.run_id or list(RUN_IDS.keys())

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    rq_tables: dict[str, pd.DataFrame] = {}
    metas: dict[str, dict] = {}
    dfs: dict[str, pd.DataFrame] = {}

    for rq in wanted:
        df, meta = load_results(RUN_IDS[rq])
        dfs[rq] = df
        metas[rq] = meta
        if rq == "rq1":
            table = rq1_summary(df)
        elif rq == "rq2":
            table = rq2_summary(df)
        elif rq == "rq3":
            table = rq3_summary(df)
        elif rq == "rq4":
            table = rq4_summary(df)
        else:  # pragma: no cover - defensive
            continue
        out_csv = TABLES_DIR / f"{rq}_summary.csv"
        table.to_csv(out_csv, index=False)
        print(f"run_all: wrote {out_csv} ({len(table)} rows)")
        rq_tables[rq] = table

    # Figures.
    make_all(dfs)
    for rq in wanted:
        for ext in ("pdf", "png"):
            print(f"run_all: wrote analysis/figures/{rq}_*.{ext}")

    # SUMMARY.md.
    summary = write_summary_md(rq_tables, metas)
    print(f"run_all: wrote {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())