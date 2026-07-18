"""Shared helpers: ids, hashing, time, concurrency primitives."""

from framework.utils.ids import new_id
from framework.utils.time import utcnow

__all__ = ["new_id", "utcnow"]