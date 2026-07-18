"""Markdown + HTML report rendering from logger events + MetricResults."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from framework.metrics.metrics import MetricResult


class Reporter:
    """Render a Markdown + HTML report from metrics and raw events."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render(
        self,
        metrics: Iterable[MetricResult],
        events: Iterable[dict[str, Any]] | None = None,
        title: str = "MCP Isolation Run Report",
    ) -> Path:
        metrics = list(metrics)
        events = list(events or [])
        md_path = self.output_dir / "report.md"
        html_path = self.output_dir / "report.html"

        md_path.write_text(self._render_md(metrics, events, title), encoding="utf-8")
        html_path.write_text(self._render_html(metrics, events, title), encoding="utf-8")
        return md_path

    @staticmethod
    def _render_md(
        metrics: list[MetricResult], events: list[dict[str, Any]], title: str
    ) -> str:
        lines = [
            f"# {title}",
            "",
            f"_Generated: {datetime.utcnow().isoformat()}Z_",
            "",
            f"**Total events:** {len(events)}",
            f"**Total (attack_id, boundary) buckets:** {len(metrics)}",
            "",
            "## Per-(attack, boundary) metrics",
            "",
            "| attack_id | boundary | leakage_rate | time_to_leak_ms | defense_overhead_ms | utility_retention | n_events |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for m in metrics:
            lines.append(
                f"| {m.attack_id} | {m.boundary} | {m.leakage_rate:.3f} | "
                f"{m.time_to_leak_ms if m.time_to_leak_ms is not None else '-'} | "
                f"{m.defense_overhead_ms if m.defense_overhead_ms is not None else '-'} | "
                f"{m.utility_retention if m.utility_retention is not None else '-'} | "
                f"{m.n_events} |"
            )
        lines.extend(
            [
                "",
                "## Raw events",
                "",
                "| timestamp | event_type | attack_id | boundary | success | tenant_pair |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for e in events:
            lines.append(
                f"| {e.get('timestamp','')} | {e.get('event_type','')} | "
                f"{e.get('attack_id','')} | {e.get('boundary','')} | "
                f"{e.get('success','')} | {e.get('tenant_pair','')} |"
            )
        return "\n".join(lines) + "\n"

    @staticmethod
    def _render_html(
        metrics: list[MetricResult], events: list[dict[str, Any]], title: str
    ) -> str:
        rows = "".join(
            f"<tr><td>{m.attack_id}</td><td>{m.boundary}</td>"
            f"<td>{m.leakage_rate:.3f}</td>"
            f"<td>{m.time_to_leak_ms if m.time_to_leak_ms is not None else '-'}</td>"
            f"<td>{m.defense_overhead_ms if m.defense_overhead_ms is not None else '-'}</td>"
            f"<td>{m.utility_retention if m.utility_retention is not None else '-'}</td>"
            f"<td>{m.n_events}</td></tr>"
            for m in metrics
        )
        ev_rows = "".join(
            f"<tr><td>{e.get('timestamp','')}</td><td>{e.get('event_type','')}</td>"
            f"<td>{e.get('attack_id','')}</td><td>{e.get('boundary','')}</td>"
            f"<td>{e.get('success','')}</td><td>{e.get('tenant_pair','')}</td></tr>"
            for e in events
        )
        return f"""<!doctype html>
<html><head><meta charset="utf-8"/><title>{title}</title>
<style>body{{font-family:sans-serif;margin:2em}}table{{border-collapse:collapse}}
td,th{{border:1px solid #888;padding:.25em .5em}}</style>
</head><body>
<h1>{title}</h1>
<p>Generated: {datetime.utcnow().isoformat()}Z</p>
<p><b>{len(events)}</b> events, <b>{len(metrics)}</b> (attack, boundary) buckets.</p>
<h2>Per-(attack, boundary) metrics</h2>
<table><tr><th>attack_id</th><th>boundary</th><th>leakage_rate</th>
<th>time_to_leak_ms</th><th>defense_overhead_ms</th><th>utility_retention</th><th>n_events</th></tr>
{rows}</table>
<h2>Raw events</h2>
<table><tr><th>timestamp</th><th>event_type</th><th>attack_id</th><th>boundary</th>
<th>success</th><th>tenant_pair</th></tr>
{ev_rows}</table>
</body></html>
"""


__all__ = ["Reporter"]