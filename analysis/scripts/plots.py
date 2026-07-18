"""Figure factory for Phase 10.

Each helper renders a matplotlib + seaborn figure, writes a
PDF + PNG pair to ``analysis/figures/``, and returns the
:class:`matplotlib.figure.Figure` for in-notebook display.

The four helpers implement the figure specs in
``prompts/10_analysis.md`` lines 63-68:

* ``rq1_leak_rate_by_boundary`` — grouped bar.
* ``rq2_cache_heatmap`` — seaborn heatmap.
* ``rq3_injection_latency`` — box+strip.
* ``rq4_defense_combo_bars`` — stacked bar.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")  # non-interactive backend (no display needed)
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

from .. import FIGURES_DIR


def _save(fig: matplotlib.figure.Figure, stem: str) -> tuple[Path, Path]:
    """Save the figure as both PDF and PNG in ``FIGURES_DIR``."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    pdf = FIGURES_DIR / f"{stem}.pdf"
    png = FIGURES_DIR / f"{stem}.png"
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(png, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return pdf, png


def rq1_leak_rate_by_boundary(
    df: pd.DataFrame, title: str = "RQ-1: Leak rate per boundary by server"
) -> matplotlib.figure.Figure:
    """Grouped bar: leak rate [%] per boundary, hue = server."""
    # Aggregate to one row per (boundary, server_variant).
    grouped = (
        df.assign(is_leak=(df["event_type"] == "leakage").astype(int))
        .groupby(["boundary", "server_variant"], as_index=False)["is_leak"]
        .mean()
        .rename(columns={"is_leak": "leak_rate"})
    )
    # Pivot so rows=boundary, cols=server.
    pivot = grouped.pivot(
        index="boundary", columns="server_variant", values="leak_rate"
    ).fillna(0.0)
    pivot = pivot * 100.0  # percent

    fig, ax = plt.subplots(figsize=(8, 4.5))
    pivot.plot(kind="bar", ax=ax, edgecolor="black", width=0.7)
    ax.set_ylabel("Leak rate [%]")
    ax.set_xlabel("Boundary")
    ax.set_title(title)
    ax.legend(title="Server", loc="best")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.xticks(rotation=30, ha="right")
    _save(fig, "rq1_leak_rate_by_boundary")
    return fig


def rq2_cache_heatmap(
    df: pd.DataFrame,
    title: str = "RQ-2: Leak count per attack on vulnerable server",
) -> matplotlib.figure.Figure:
    """Heatmap: rows = attack, columns = defense, values = leak count."""
    cch = df[df["attack_id"].str.startswith("A-CCH-") | (df["attack_id"] == "A-FUZZ-001")]
    if cch.empty:
        raise ValueError("RQ-2 requires A-CCH-* or A-FUZZ-001 rows")
    pivot = (
        cch[cch["event_type"] == "leakage"]
        .groupby(["attack_id", "server_variant"], as_index=False)
        .size()
        .pivot(index="attack_id", columns="server_variant", values="size")
        .fillna(0)
        .astype(int)
    )
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.heatmap(pivot, annot=True, fmt="d", cmap="Reds", cbar=True, ax=ax)
    ax.set_title(title)
    ax.set_xlabel("Server variant")
    ax.set_ylabel("Attack id")
    plt.xticks(rotation=20, ha="right")
    plt.yticks(rotation=0)
    _save(fig, "rq2_cache_heatmap")
    return fig


def rq3_injection_latency(
    df: pd.DataFrame,
    title: str = "RQ-3: Prompt-injection latency per attack (secure)",
) -> matplotlib.figure.Figure:
    """Box+strip: per-attack latency on the secure server."""
    secure = df[df["server_variant"] == "secure"].copy()
    if secure.empty:
        raise ValueError("RQ-3 requires secure server rows")
    secure["latency_ms"] = pd.to_numeric(secure["latency_ms"], errors="coerce")
    attacks = sorted(secure["attack_id"].unique())
    fig, ax = plt.subplots(figsize=(9, 4.5))
    data = [secure[secure["attack_id"] == a]["latency_ms"].dropna().values for a in attacks]
    sns.boxplot(data=data, ax=ax, whis=1.5, showfliers=False)
    sns.stripplot(data=data, ax=ax, color="black", alpha=0.4, size=3)
    ax.set_xticks(range(len(attacks)))
    ax.set_xticklabels(attacks, rotation=30, ha="right")
    ax.set_ylabel("Latency [ms]")
    ax.set_title(title)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    _save(fig, "rq3_injection_latency")
    return fig


def rq4_defense_combo_bars(
    df: pd.DataFrame,
    title: str = "RQ-4: Leak rate per defense level by attack",
) -> matplotlib.figure.Figure:
    """Stacked bar: leak rate per defense level, hue = attack.

    Defense levels appear on the X-axis; each attack gets a bar
    segment inside each level.
    """
    grouped = (
        df.assign(is_leak=(df["event_type"] == "leakage").astype(int))
        .groupby(["defense_level", "attack_id"], as_index=False)["is_leak"]
        .mean()
        .rename(columns={"is_leak": "leak_rate"})
    )
    pivot = grouped.pivot(
        index="defense_level", columns="attack_id", values="leak_rate"
    ).fillna(0.0) * 100.0
    # Stable order: none / partial (per_tenant) / full.
    desired = ["none", "partial", "per_tenant", "full"]
    pivot = pivot.reindex([d for d in desired if d in pivot.index])
    fig, ax = plt.subplots(figsize=(9, 4.5))
    pivot.plot(kind="bar", stacked=True, ax=ax, edgecolor="black", width=0.6)
    ax.set_ylabel("Leak rate [%]")
    ax.set_xlabel("Defense level")
    ax.set_title(title)
    ax.legend(title="Attack", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.xticks(rotation=0)
    _save(fig, "rq4_defense_combo_bars")
    return fig


def make_all(df_by_rq: dict[str, pd.DataFrame]) -> dict[str, matplotlib.figure.Figure]:
    """Render all four figures. ``df_by_rq`` keys: rq1..rq4."""
    out: dict[str, matplotlib.figure.Figure] = {}
    if "rq1" in df_by_rq:
        out["rq1"] = rq1_leak_rate_by_boundary(df_by_rq["rq1"])
    if "rq2" in df_by_rq:
        out["rq2"] = rq2_cache_heatmap(df_by_rq["rq2"])
    if "rq3" in df_by_rq:
        out["rq3"] = rq3_injection_latency(df_by_rq["rq3"])
    if "rq4" in df_by_rq:
        out["rq4"] = rq4_defense_combo_bars(df_by_rq["rq4"])
    return out


__all__ = [
    "make_all",
    "rq1_leak_rate_by_boundary",
    "rq2_cache_heatmap",
    "rq3_injection_latency",
    "rq4_defense_combo_bars",
]


# Typing for the stub above (kept off the runtime signature).
_ = Any
