"""Payload generator for the MCP isolation framework.

Phase-6 ships a deterministic per-recipe placeholder mutator.
Phase 7 will replace per-recipe mutators with concrete ones
sourced from the ``attacks`` package.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AttackRecipe:
    """A concrete, runnable attack payload description."""

    id: str
    boundary: str
    category: str
    parameters: dict[str, Any] = field(default_factory=dict)
    success_criteria: list[dict[str, Any]] = field(default_factory=list)

    def payload_sha256(self, payload: str) -> str:
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class PayloadGenerator:
    """Deterministic per-(recipe, seed) payload generator.

    Phase-6 placeholder behaviour: every recipe produces a single
    payload that is a JSON line encoding the recipe id + seed +
    parameters. Phase-7 mutators will replace the body of
    :meth:`generate` for each recipe id.
    """

    def __init__(self, seed: int = 0) -> None:
        self.seed = seed

    def generate(self, recipe: AttackRecipe) -> list[str]:
        """Return one or more payload strings for the given recipe."""
        # Derive a deterministic int seed from (self.seed, recipe.id).
        derived_seed = (self.seed * 1_000_003) ^ (hash(recipe.id) & 0xFFFFFFFF)
        rng = random.Random(derived_seed)
        # Phase-6 placeholder: deterministic JSON. Real Phase-7
        # generators will mutate by recipe category.
        import json

        payload = json.dumps(
            {
                "recipe_id": recipe.id,
                "boundary": recipe.boundary,
                "category": recipe.category,
                "seed": self.seed,
                "nonce": rng.randrange(1 << 32),
                "parameters": recipe.parameters,
                "marker": f"MCP-ISO-{recipe.id}-{self.seed:04d}",
            },
            sort_keys=True,
        )
        return [payload]

    def generate_batch(self, recipes: list[AttackRecipe]) -> list[tuple[AttackRecipe, str]]:
        out: list[tuple[AttackRecipe, str]] = []
        for r in recipes:
            for p in self.generate(r):
                out.append((r, p))
        return out


__all__ = ["AttackRecipe", "PayloadGenerator"]