"""Pytest fixtures for the MCP isolation framework."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from attacks._helpers import AttackContext  # noqa: E402
from framework.target.connector import DummyConnector  # noqa: E402


@pytest.fixture
def event_loop() -> asyncio.AbstractEventLoop:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def dummy_connectors() -> tuple[DummyConnector, DummyConnector]:
    """A (source, sink) pair with leak injection enabled on the sink."""
    source = DummyConnector("tenant-A", leak_probability=0.0)
    sink = DummyConnector("tenant-B", leak_probability=1.0)
    source.connect()
    sink.connect()
    return source, sink


@pytest.fixture
def attack_context(dummy_connectors) -> AttackContext:
    source, sink = dummy_connectors
    return AttackContext(
        source_connector=source,
        sink_connector=sink,
        payload_marker="MCP-ISO-A-TRN-S-0042",
        seed=42,
        parameters={},
    )