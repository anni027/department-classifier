"""Pure scoring functions: trait normalisation/update, department scoring, softmax.

No classes — each function has exactly one job and no state to hide.
"""
from __future__ import annotations

import math

from app.core.models import Department

INITIAL_TRAIT_SCORE = 0.5
LEARNING_RATE = 0.4
SECONDARY_LEARNING_MULTIPLIER = 0.5  # secondary LR = LEARNING_RATE * this = 0.2


def normalize_answer(value: int) -> float:
    """Map a 1-5 Likert answer to 0.0-1.0."""
    return (value - 1) / 4


def update_trait_scores(
    trait_scores: dict[str, float],
    primary_trait: str,
    secondary_traits: list[str],
    answer_value: int,
    learning_rate: float = LEARNING_RATE,
    secondary_multiplier: float = SECONDARY_LEARNING_MULTIPLIER,
) -> dict[str, float]:
    """Return a NEW trait_scores dict with primary/secondary traits updated.

    primary:   new = old*(1-lr)      + normalized*lr
    secondary: new = old*(1-lr*mult) + normalized*(lr*mult)
    """
    normalized = normalize_answer(answer_value)
    updated = dict(trait_scores)

    old_primary = updated[primary_trait]
    updated[primary_trait] = old_primary * (1 - learning_rate) + normalized * learning_rate

    secondary_lr = learning_rate * secondary_multiplier
    for trait in secondary_traits:
        old = updated[trait]
        updated[trait] = old * (1 - secondary_lr) + normalized * secondary_lr

    return {trait: min(1.0, max(0.0, score)) for trait, score in updated.items()}


def department_score(trait_scores: dict[str, float], department: Department) -> float:
    """Raw weighted score = sum(user_trait * department_weight) over all traits."""
    return sum(trait_scores[trait] * weight for trait, weight in department.weights.items())


def softmax(scores: dict[str, float]) -> dict[str, float]:
    """Numerically stable softmax over a {key: score} mapping."""
    max_score = max(scores.values())
    exp_scores = {key: math.exp(score - max_score) for key, score in scores.items()}
    total = sum(exp_scores.values())
    return {key: value / total for key, value in exp_scores.items()}
