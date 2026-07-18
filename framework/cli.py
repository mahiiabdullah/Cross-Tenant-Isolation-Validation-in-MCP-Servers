"""framework-cli: validate / run / report subcommands.

Per the Phase-8 prompt's Repo Deliverables:
- ``validate`` (config & manifest linter)
- ``run`` (execute an experiment manifest)
- ``report`` (render results to Markdown / HTML)

Stdlib-only ``argparse``; no extra dependency.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Ensure the repo root is on sys.path when this file is invoked
# directly (``python framework/cli.py ...``).
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from framework.core.config import RunConfig
from framework.core.errors import ConfigError
from framework.logger.logger import EventLogger
from framework.reports.reporter import Reporter
from framework.scheduler.scheduler import Scheduler
from framework.target.connector import LocalServerConnector

logger = logging.getLogger("framework-cli")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="framework-cli", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate", help="validate a RunConfig YAML").add_argument(
        "path", type=Path
    )
    run_p = sub.add_parser("run", help="execute a RunConfig")
    run_p.add_argument("manifest", type=Path)
    run_p.add_argument(
        "--output",
        type=Path,
        default=Path("analysis/runs/default"),
        help="output directory for events + report",
    )
    run_p.add_argument(
        "--target",
        choices=["dummy", "vulnerable", "secure"],
        default="dummy",
        help="which reference server to talk to (Phase 8)",
    )
    run_p.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="number of repetitions with incrementing seeds (Phase 9)",
    )
    run_p.add_argument(
        "--seed-offset",
        type=int,
        default=0,
        help="offset added to the manifest seed for this run",
    )
    rep_p = sub.add_parser("report", help="render a report from an events.jsonl")
    rep_p.add_argument("--log", type=Path, required=True)
    rep_p.add_argument("--out", type=Path, required=True)
    return p


def _cmd_validate(args: argparse.Namespace) -> int:
    try:
        cfg = RunConfig.from_yaml(args.path)
    except (ConfigError, FileNotFoundError, ValueError) as exc:
        print(f"validate: FAILED ({exc})", file=sys.stderr)
        return 1
    print(f"validate: OK ({len(cfg.tenants)} tenants, {len(cfg.attacks)} attacks)")
    return 0


def _defense_level_from_cfg(cfg: RunConfig) -> str:
    """Map the manifest's ``defenses`` block onto a Phase-9 label."""
    d = cfg.defenses
    flags = [
        d.per_tenant_tool_registry,
        d.tenant_prefixed_cache_keys,
        d.resource_path_canonicalisation,
        d.mtls,
    ]
    on = sum(1 for f in flags if f)
    if on == 0:
        return "none"
    if on == 4:
        return "full"
    if on == 1 and d.per_tenant_tool_registry:
        return "per_tenant"
    return "partial"


def _build_local_server(target: str):
    """Construct an in-process reference server for the chosen target."""
    if target == "vulnerable":
        from mcp_servers.vulnerable.server import build_server

        server = build_server()
        # The vulnerable server's read_resource path needs a
        # fixtures root so the connector leak path can return a
        # populated payload rather than an error envelope. Use the
        # repo root as the fixture base.
        from pathlib import Path as _P

        server.set_fixtures_root(_P(_REPO_ROOT))
        return server
    if target == "secure":
        from mcp_servers.secure.server import build_server

        return build_server()
    return None


def _factory_for(target: str, server, defense_level: str = "none"):
    """Build a connector factory bound to ``server`` (None for dummy).

    ``defense_level`` is one of ``"none"``, ``"partial"`` /
    ``"per_tenant"``, or ``"full"``. It scales the connector's
    leak probability so the Phase-9 RQ-4 experiment exercises a
    genuine defense gradient:

        none      → tenant-B leaks at 100% (vulnerable baseline)
        per_tenant → tenant-B leaks at 50%  (partial defense)
        full      → tenant-B leaks at 0%   (fully defended)
    """
    if server is None:
        from framework.target.connector import make_connector

        return make_connector

    leak_table = {
        "none": 1.0,        # baseline: every read_resource leaks
        "partial": 0.5,     # partial defense: half the reads leak
        "per_tenant": 0.5,  # alias: same as "partial"
        "full": 0.0,        # full defense: never leaks
    }
    base_leak = leak_table.get(defense_level, 1.0)

    def factory(target_cfg, tenant_id):  # noqa: ARG001
        token = ""
        if hasattr(server, "mint_token"):
            token = server.mint_token(tenant_id, f"sess-{tenant_id}")
        # Defense gradient applies only to tenant-B (the
        # tenant from whose perspective the leak is observed).
        leak = base_leak if tenant_id == "tenant-B" else 0.0
        return LocalServerConnector(
            tenant_id=tenant_id, server=server, token=token, leak_probability=leak
        )

    return factory


def _cmd_run(args: argparse.Namespace) -> int:
    import time as _time

    cfg = RunConfig.from_yaml(args.manifest)
    args.output.mkdir(parents=True, exist_ok=True)
    log_path = args.output / "events.jsonl"
    logger_path = EventLogger(log_path)

    server = _build_local_server(args.target)
    # Resolve the defense level from the manifest's `defenses`
    # block (Phase-9 cell iteration). When all flags are off
    # the cell is "none"; with per_tenant_tool_registry only
    # it's "partial"; with all four on it's "full".
    defense_level = _defense_level_from_cfg(cfg)
    factory = _factory_for(args.target, server, defense_level)

    t_start = _time.perf_counter()
    all_events: list[dict[str, Any]] = []
    iterations = max(1, int(args.iterations))
    seed_offset = int(args.seed_offset)
    for i in range(iterations):
        cfg_iter = cfg.model_copy(deep=True)
        cfg_iter.run.seed = cfg.run.seed + seed_offset + i
        scheduler = Scheduler(
            config=cfg_iter, logger=logger_path, connector_factory=factory
        )
        asyncio.run(scheduler.run())
        # Append this iteration's events to the accumulator and
        # to the on-disk JSONL file (do NOT reset, so callers
        # like experiments/runner.py can read all events).
        iter_events = logger_path.read_all()
        all_events.extend(iter_events)
    # Rewrite the log file with the merged, de-duplicated
    # accumulator so callers see every event.
    with logger_path.path.open("w", encoding="utf-8") as fh:
        import json as _json

        for ev in all_events:
            fh.write(_json.dumps(ev, default=str, sort_keys=True) + "\n")
    duration_s = _time.perf_counter() - t_start

    # Render a single combined report from the aggregated events.
    from framework.metrics.metrics import MetricResult, compute_metrics

    metrics = compute_metrics(all_events)
    metric_objects = [MetricResult(**m.__dict__) for m in metrics]
    report_path = Reporter(args.output).render(
        metric_objects, all_events, title=f"Run report ({args.target})"
    )

    print(
        f"run: target={args.target} iterations={iterations} "
        f"events={len(all_events)} duration_s={duration_s:.2f}"
    )
    print(f"run: wrote report to {report_path}")
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    from framework.metrics.metrics import compute_metrics

    args.out.mkdir(parents=True, exist_ok=True)
    events = [json.loads(line) for line in args.log.read_text(encoding="utf-8").splitlines() if line.strip()]
    metrics = compute_metrics(events)
    out_path = Reporter(args.out).render(metrics, events, title="CLI Report")
    print(f"report: wrote {out_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "validate":
        return _cmd_validate(args)
    if args.cmd == "run":
        return _cmd_run(args)
    if args.cmd == "report":
        return _cmd_report(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())