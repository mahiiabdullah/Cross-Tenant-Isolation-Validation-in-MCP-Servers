"""Attack registry.

Discovers concrete :class:`attacks.base.Attack` subclasses by
walking the ``attacks/<boundary>/`` subpackages and indexing
them by their ``id`` attribute (e.g. ``"A-TRN-S"``,
``"A-RES-001"``).

Phase 9 will materialise the experiment matrix from this
registry.
"""

from __future__ import annotations

import importlib
from typing import Any

from attacks.base import Attack
from framework.core.types import Boundary


def _walk_subpackages() -> list[str]:
    """Return fully-qualified module names for all leaf ``attacks.*`` modules.

    We do a manual DFS rather than ``pkgutil.walk_packages`` because
    ``walk_packages`` only recurses into packages that have been
    imported already (or are listed in ``__all__``). Since
    ``attacks/__init__.py`` is a bare docstring, the recursion stops
    at the first level.
    """
    import attacks
    from pathlib import Path

    out: list[str] = []
    seen: set[str] = set()

    def visit(package_path: Path, prefix: str) -> None:
        for entry in sorted(package_path.iterdir()):
            if entry.name.startswith("__") or entry.name.startswith("."):
                continue
            if entry.is_file() and entry.suffix == ".py":
                mod_name = entry.stem
                fqn = f"{prefix}.{mod_name}" if prefix else mod_name
                if fqn not in seen:
                    seen.add(fqn)
                    out.append(fqn)
            elif entry.is_dir():
                sub_prefix = f"{prefix}.{entry.name}" if prefix else entry.name
                visit(entry, sub_prefix)

    visit(Path(attacks.__path__[0]), "attacks")
    return out


def _discover_classes() -> dict[str, type[Attack]]:
    """Walk the attacks tree and collect concrete Attack subclasses by id."""
    out: dict[str, type[Attack]] = {}
    for module_name in _walk_subpackages():
        try:
            mod = importlib.import_module(module_name)
        except Exception:
            continue
        for attr_name in dir(mod):
            cls = getattr(mod, attr_name, None)
            if cls is None or not isinstance(cls, type):
                continue
            if not issubclass(cls, Attack):
                continue
            if cls is Attack:
                continue
            if not getattr(cls, "id", None):
                continue
            if cls.id in out:
                # Idempotent: first registration wins.
                continue
            out[cls.id] = cls
    return out


REGISTRY: dict[str, type[Attack]] = _discover_classes()


def get_attack(attack_id: str) -> type[Attack]:
    """Look up an attack class by id."""
    cls = REGISTRY.get(attack_id)
    if cls is None:
        raise KeyError(
            f"no attack registered with id {attack_id!r}; "
            f"known ids: {sorted(REGISTRY)}"
        )
    return cls


def list_ids() -> list[str]:
    """Return all registered attack ids, sorted."""
    return sorted(REGISTRY)


def attacks_by_boundary() -> dict[Boundary, list[type[Attack]]]:
    """Group registered attack classes by their boundary."""
    out: dict[Boundary, list[type[Attack]]] = {b: [] for b in Boundary}
    for cls in REGISTRY.values():
        out[cls.boundary].append(cls)
    return out


def coverage_report() -> dict[str, Any]:
    """Return a coverage summary: counts and per-boundary breakdown."""
    by_b = attacks_by_boundary()
    return {
        "total": len(REGISTRY),
        "per_boundary": {b.value: len(v) for b, v in by_b.items()},
        "ids": list_ids(),
    }


__all__ = [
    "REGISTRY",
    "attacks_by_boundary",
    "coverage_report",
    "get_attack",
    "list_ids",
]