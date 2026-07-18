"""Tests for framework.core.errors."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from framework.core.errors import (  # noqa: E402
    AttackError,
    ConfigError,
    EvaluatorError,
    MCPIsolationError,
    ManifestError,
    TransportError,
)


def test_config_error_is_isolation_error() -> None:
    assert issubclass(ConfigError, MCPIsolationError)


def test_attack_error_is_isolation_error() -> None:
    assert issubclass(AttackError, MCPIsolationError)


def test_evaluator_error_is_isolation_error() -> None:
    assert issubclass(EvaluatorError, MCPIsolationError)


def test_transport_error_is_isolation_error() -> None:
    assert issubclass(TransportError, MCPIsolationError)


def test_manifest_error_is_isolation_error() -> None:
    assert issubclass(ManifestError, MCPIsolationError)


def test_can_raise_and_catch() -> None:
    with __import__("pytest").raises(MCPIsolationError):
        raise ConfigError("bad config")