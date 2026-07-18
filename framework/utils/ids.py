"""ID generation helpers."""

from __future__ import annotations

from uuid import uuid4


def new_id(prefix: str = "id") -> str:
    """Return a short prefixed UUID4 string."""
    return f"{prefix}-{uuid4().hex[:12]}"