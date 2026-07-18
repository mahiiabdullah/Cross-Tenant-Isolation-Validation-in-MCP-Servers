"""Filesystem helpers.

Per the Phase-8 Code-Gen Rules, **all** I/O lives here. No other
module may call :func:`open`, :meth:`Path.read_text`, or
:meth:`Path.write_text` directly.
"""

from __future__ import annotations

from pathlib import Path


def safe_read_text(path: str | Path) -> str:
    """Read a UTF-8 text file. Returns ``""`` for empty files."""
    p = Path(path)
    return p.read_text(encoding="utf-8")


def safe_write_text(path: str | Path, content: str) -> None:
    """Write UTF-8 text to ``path`` atomically (parent dir is created)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def ensure_dir(path: str | Path) -> Path:
    """Create ``path`` (and parents) if it does not exist; return it."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


__all__ = ["ensure_dir", "safe_read_text", "safe_write_text"]