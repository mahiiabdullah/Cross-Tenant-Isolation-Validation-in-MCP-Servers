"""Structured JSONL event logger.

Thread-safe append of validated event dicts to a JSONL file.
Phase 9 will replace ``emit`` with an async-aware version that
also fans out to loguru.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

REQUIRED_KEYS: ClassVar[set[str]] = {
    "timestamp",
    "event_type",
    "attack_id",
    "boundary",
    "tenant_pair",
    "seed",
    "payload_sha256",
    "latency_ms",
    "success",
}


class EventLogger:
    """Append-only JSONL event logger with schema validation."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        # Touch the file so the smoke test can assert existence.
        self.path.touch(exist_ok=True)

    def emit(self, event: dict[str, Any]) -> None:
        """Append a single validated event as one JSON line."""
        missing = REQUIRED_KEYS - set(event.keys())
        if missing:
            raise ValueError(f"event missing required keys: {sorted(missing)}")
        event = dict(event)
        if not isinstance(event.get("timestamp"), (str, datetime)):
            event["timestamp"] = datetime.utcnow().isoformat()
        line = json.dumps(event, default=str, sort_keys=True)
        with self._lock:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")

    def read_all(self) -> list[dict[str, Any]]:
        """Return all events written so far."""
        if not self.path.exists():
            return []
        out: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                out.append(json.loads(line))
        return out


__all__ = ["EventLogger"]