"""Isolation measurement framework for MCP.

This package is structured around:

- :mod:`framework.core` — domain types (Tenant, Session, Boundary, ...).
- :mod:`framework.scheduler` — concurrent tenant + attack scheduling.
- :mod:`framework.evaluator` — decides whether an attack produced leakage.
- :mod:`framework.metrics` — aggregates results into metrics.
- :mod:`framework.logger` — structured event logging.
- :mod:`framework.reports` — renders reports from logger output.
- :mod:`framework.utils` — shared helpers.
"""

__version__ = "0.2.0"