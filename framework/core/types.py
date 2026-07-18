"""Pydantic-backed domain types used across the framework.

These types are intentionally minimal — concrete fields can be expanded as
attacks and defenses are implemented.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Boundary(str, Enum):
    """Isolation boundaries studied in this project."""

    TRANSPORT = "transport"
    SESSION = "session"
    NAMESPACE = "namespace"
    TOOL = "tool"
    RESOURCE = "resource"
    MEMORY = "memory"
    CACHE = "cache"
    AUTH = "auth"


class Tenant(BaseModel):
    """A logical principal using an MCP server."""

    id: str = Field(default_factory=lambda: f"tenant-{uuid4().hex[:8]}")
    name: str = "unnamed"
    allowed_tools: set[str] = Field(default_factory=set)
    allowed_resources: set[str] = Field(default_factory=set)


class Session(BaseModel):
    """A server-side session bound to one tenant."""

    id: str = Field(default_factory=lambda: f"sess-{uuid4().hex[:8]}")
    tenant_id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)


class ToolCall(BaseModel):
    """A single tool invocation event."""

    id: str = Field(default_factory=lambda: f"call-{uuid4().hex[:8]}")
    tenant_id: str
    session_id: str
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: Any = None
    boundary_crossed: Boundary | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class LeakageEvent(BaseModel):
    """An observed cross-tenant data flow."""

    id: str = Field(default_factory=lambda: f"leak-{uuid4().hex[:8]}")
    source_tenant: str
    sink_tenant: str
    boundary: Boundary
    payload_excerpt: str = ""
    confidence: float = 1.0
    detected_at: datetime = Field(default_factory=datetime.utcnow)