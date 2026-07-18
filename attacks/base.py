"""Shared base classes for attack implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from framework.core.types import Boundary


@dataclass
class AttackResult:
    """Outcome of a single attack run."""

    success: bool
    boundary: Boundary
    detail: dict[str, Any] | None = None


class Attack:
    """Base class for all attacks.

    Subclasses MUST set ``id`` and ``boundary`` and implement
    :meth:`execute`.
    """

    id: str = "base"
    boundary: Boundary = Boundary.TOOL

    async def setup(self, ctx: Any) -> None:  # pragma: no cover - default no-op
        return None

    async def execute(self, ctx: Any) -> AttackResult:  # pragma: no cover
        raise NotImplementedError

    async def teardown(self, ctx: Any) -> None:  # pragma: no cover - default no-op
        return None