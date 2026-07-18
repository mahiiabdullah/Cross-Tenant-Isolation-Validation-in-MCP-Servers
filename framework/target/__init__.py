"""Target MCP server connectors.

Provides:

- :class:`MCPConnector` abstract base class for real transports
  (HTTP+SSE, stdio, streamable HTTP) — implementations land in
  Phase 8.
- :class:`DummyConnector` in-process tenant-scoped simulator used
  by the Phase-6 smoke test. It can be configured to **simulate
  leakage** by returning another tenant's payload on demand.
- :func:`make_connector` factory that selects a connector by
  transport name from the Phase-6 ``RunConfig.target`` block.
"""

from framework.target.connector import (
    DummyConnector,
    MCPConnector,
    make_connector,
)

__all__ = ["DummyConnector", "MCPConnector", "make_connector"]