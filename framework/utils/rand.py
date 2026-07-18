"""Deterministic RNG helper."""

from __future__ import annotations

import random


def seeded_rng(seed: int) -> random.Random:
    """Return a :class:`random.Random` instance seeded with ``seed``.

    Phase-8 Code-Gen Rule: any module that needs randomness MUST
    use this helper so that experiments are reproducible across
    machines and Python versions.
    """
    return random.Random(int(seed))


__all__ = ["seeded_rng"]