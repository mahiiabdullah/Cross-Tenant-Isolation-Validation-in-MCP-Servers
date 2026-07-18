"""Time helpers."""

from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Timezone-aware UTC ``datetime``."""
    return datetime.now(timezone.utc)