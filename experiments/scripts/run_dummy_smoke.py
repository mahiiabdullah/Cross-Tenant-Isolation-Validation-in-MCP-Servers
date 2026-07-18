"""Phase-6 end-to-end smoke test.

Loads ``experiments/configs/example_run.yaml``, drives one
attack through the harness, asserts that the JSONL log contains
at least one event, and that the Markdown report was written.

Usage:
    python experiments/scripts/run_dummy_smoke.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from framework.core.config import RunConfig  # noqa: E402
from framework.logger.logger import EventLogger  # noqa: E402
from framework.scheduler.scheduler import run_sync  # noqa: E402
from framework.target.connector import DummyConnector  # noqa: E402


def main() -> int:
    cfg = RunConfig.from_yaml(REPO / "experiments" / "configs" / "example_run.yaml")
    print("Loaded RunConfig:")
    print(json.dumps(cfg.model_dump(mode="json"), indent=2))

    # Configure the dummy connector to simulate leakage so the
    # evaluator can fire.
    log_path = cfg.output.log_dir / "example_run.jsonl"
    logger = EventLogger(log_path)

    # Wrap the connector factory so Tenant A is configured to leak.
    original_factory = cfg.target

    def factory(target, tenant_id):  # noqa: ARG001
        # The sink tenant's connector is configured to leak so the
        # Evaluator can detect cross-tenant data flow.
        return DummyConnector(
            tenant_id=tenant_id,
            leak_probability=1.0 if tenant_id == "tenant-B" else 0.0,
        )

    # Re-instantiate scheduler with the wrapped factory.
    from framework.scheduler.scheduler import Scheduler

    scheduler = Scheduler(config=cfg, logger=logger, connector_factory=factory)
    import asyncio

    summary = asyncio.run(scheduler.run())

    print("\nRunSummary:")
    print(json.dumps(summary.model_dump(), indent=2))

    events = logger.read_all()
    assert events, "smoke test failed: no events were emitted"
    print(f"\nEmitted {len(events)} events to {log_path}")

    md_path = Path(summary.report_paths["markdown"])
    assert md_path.exists(), f"smoke test failed: report not written at {md_path}"
    print(f"Markdown report: {md_path}")

    print("\nSmoke test PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())