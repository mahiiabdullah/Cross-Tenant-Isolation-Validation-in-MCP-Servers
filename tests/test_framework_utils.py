"""Tests for framework.utils (io + rand)."""

from __future__ import annotations

import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from framework.utils.io import ensure_dir, safe_read_text, safe_write_text  # noqa: E402
from framework.utils.rand import seeded_rng  # noqa: E402


def test_safe_write_then_read_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "nested" / "f.txt"
    safe_write_text(p, "hello")
    assert safe_read_text(p) == "hello"


def test_ensure_dir_creates_parents(tmp_path: Path) -> None:
    p = tmp_path / "a" / "b" / "c"
    out = ensure_dir(p)
    assert out.is_dir()
    assert out == p


def test_seeded_rng_is_deterministic() -> None:
    a = seeded_rng(123)
    b = seeded_rng(123)
    assert [a.randrange(1000) for _ in range(5)] == [b.randrange(1000) for _ in range(5)]


def test_seeded_rng_differs_per_seed() -> None:
    a = seeded_rng(1)
    b = seeded_rng(2)
    assert a.randrange(10**9) != b.randrange(10**9)