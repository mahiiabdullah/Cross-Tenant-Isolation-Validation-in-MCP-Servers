"""Tests for the attack library.

Validates the Phase 7 Done-When gates:

- ≥25 distinct attack classes registered.
- Each of the 8 ``Boundary`` enum values has ≥1 attack.
- Each registered class has a CVSS vector (class attr or docstring).
- Each registered class instantiates and is callable.
"""

from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from attacks.base import Attack  # noqa: E402
from attacks.registry import REGISTRY, list_ids  # noqa: E402
from framework.core.types import Boundary  # noqa: E402

ID_PATTERN = re.compile(r"^A-[A-Z]{3,4}-[A-Z0-9]{1,3}$")
CVSS_PATTERN = re.compile(r"CVSS:3\.1/")


def test_minimum_attack_count() -> None:
    ids = list_ids()
    assert len(ids) >= 25, f"expected ≥25 attacks, got {len(ids)}"


def test_every_boundary_has_at_least_one_attack() -> None:
    seen = {cls.boundary for cls in REGISTRY.values()}
    missing = set(Boundary) - seen
    assert not missing, f"boundaries with no registered attack: {missing}"


@pytest.mark.parametrize("attack_id", sorted(REGISTRY))
def test_attack_id_format(attack_id: str) -> None:
    assert ID_PATTERN.match(attack_id), f"bad id format: {attack_id}"


@pytest.mark.parametrize("attack_id", sorted(REGISTRY))
def test_attack_has_cvss(attack_id: str) -> None:
    cls = REGISTRY[attack_id]
    cvss = getattr(cls, "cvss", None)
    if not cvss:
        doc = (cls.__doc__ or "") + " " + (getattr(cls, "__init__", type("X", (), {"__doc__": ""}))).__doc__
        assert CVSS_PATTERN.search(doc), f"no CVSS vector on class {cls.__name__}"
    else:
        assert CVSS_PATTERN.search(cvss), f"malformed cvss attr on {cls.__name__}: {cvss!r}"


@pytest.mark.parametrize("attack_id", sorted(REGISTRY))
def test_attack_subclasses_attack_base(attack_id: str) -> None:
    cls = REGISTRY[attack_id]
    assert issubclass(cls, Attack), f"{cls.__name__} is not an Attack subclass"
    assert cls is not Attack


@pytest.mark.parametrize("attack_id", sorted(REGISTRY))
def test_attack_instantiable(attack_id: str) -> None:
    cls = REGISTRY[attack_id]
    instance = cls()
    assert hasattr(instance, "execute")
    assert callable(instance.execute)


def test_attack_execute_runs(attack_context) -> None:
    """Pick one representative attack and run it end-to-end."""
    from attacks.registry import get_attack

    cls = get_attack("A-TRN-S")
    result = asyncio.run(cls().execute(attack_context))
    assert result.boundary == Boundary.TRANSPORT
    assert isinstance(result.success, bool)
    assert isinstance(result.detail, dict)


def test_no_duplicate_ids() -> None:
    ids = list_ids()
    assert len(ids) == len(set(ids)), "duplicate attack ids registered"