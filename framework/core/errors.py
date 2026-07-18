"""Typed exception hierarchy for the MCP isolation framework."""

from __future__ import annotations


class MCPIsolationError(Exception):
    """Base class for all framework-level errors."""


class ConfigError(MCPIsolationError):
    """A :class:`framework.core.config.RunConfig` failed validation."""


class AttackError(MCPIsolationError):
    """An attack raised during setup / execute / teardown."""


class EvaluatorError(MCPIsolationError):
    """The Evaluator oracle failed to classify a result."""


class TransportError(MCPIsolationError):
    """A transport-level (stdio / HTTP+SSE) failure occurred."""


class ManifestError(MCPIsolationError):
    """A frozen manifest (signed or unsigned) failed to load."""


__all__ = [
    "AttackError",
    "ConfigError",
    "EvaluatorError",
    "MCPIsolationError",
    "ManifestError",
    "TransportError",
]