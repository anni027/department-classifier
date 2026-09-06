"""Pure scoring functions: trait estimation, department scoring, softmax.

No classes — each function has exactly one job and no state to hide.
"""
from __future__ import annotations

import math

from app.core.models import Department, Question

INITIAL_TRAIT_SCORE = 0.5

# Weight of the 0.5 prior, in units of "one answer". At 0.6 a single maximal
# answer moves a trait from 0.5 to 0.8125 rather than all the way to 1.0, so
# one stray click can't dominate a trait, but a couple of consistent answers
# still can.
PRIOR_WEIGHT = 0.6
# An answer counts fully for its primary trait and half for each secondary,
# preserving the 2:1 ratio of the learning rates this replaced (0.4 vs 0.2).
SECONDARY_WEIGHT = 0.5

# Softmax temperature for classification. This is THE tuning knob for how
# decisive the quiz is: at 0.05 roughly 87% of sessions stop at the
# 8-question minimum (mean 8.5 questions). Raising it flattens the
# probabilities, so the quiz asks more questions and reports lower
# confidence; lowering it does the reverse.
TEMPERATURE = 0.05


def normalize_answer(value: int) -> float:
    """Map a 1-5 Likert answer to 0.0-1.0."""
    return (value - 1) / 4


def compute_trait_scores(
    responses: dict[str, int],
    questions_by_id: dict[str, Question],
    traits: list[str],
) -> dict[str, float]:
    """Rebuild the ENTIRE trait vector from the full response history.

    Each trait is the weighted mean of the 0.5 prior (at PRIOR_WEIGHT) and
    every answer that touched it (weight 1.0 as primary, SECONDARY_WEIGHT as
    secondary). A trait no question touched keeps exactly the prior.

    This replaces an incremental learning-rate update, under which each new
    answer pulled a trait a fixed fraction of the way toward itself and so
    counted for more than the answers before it — the same twelve answers in
    a different order gave a different recommendation 52.7% of the time.
    Here the answers are summed, and addition is commutative, so
    order-independence holds by construction rather than by luck.

    No clamping is needed: a weighted mean of values in [0, 1] is in [0, 1].
    """
    # trait -> [weighted_sum, total_weight], seeded with the prior.
    accumulators: dict[str, list[float]] = {
        trait: [INITIAL_TRAIT_SCORE * PRIOR_WEIGHT, PRIOR_WEIGHT] for trait in traits
    }

    for question_id, answer_value in responses.items():
        question = questions_by_id[question_id]
        normalized = normalize_answer(answer_value)
        weighted_traits = [(question.primary_trait, 1.0)]
        weighted_traits += [(trait, SECONDARY_WEIGHT) for trait in question.secondary_traits]

        for trait, weight in weighted_traits:
            accumulator = accumulators[trait]
            accumulator[0] += normalized * weight
            accumulator[1] += weight

    return {
        trait: weighted_sum / total_weight
        for trait, (weighted_sum, total_weight) in accumulators.items()
    }


def _mean_centred(values: list[float]) -> list[float]:
    mean = sum(values) / len(values)
    return [value - mean for value in values]


def department_affinity(trait_scores: dict[str, float], department: Department) -> float:
    """Cosine similarity between the mean-centred trait and weight vectors.

    Centring is what makes this a fit measure rather than a popularity
    contest: it compares the SHAPE of the two profiles (which traits stand
    out relative to the rest) instead of their magnitude, so a department
    with broadly high weights no longer outscores every specialist before
    the first question is answered.
    """
    traits = list(department.weights)
    user_vector = _mean_centred([trait_scores[trait] for trait in traits])
    dept_vector = _mean_centred([department.weights[trait] for trait in traits])

    user_norm = math.sqrt(sum(value * value for value in user_vector))
    dept_norm = math.sqrt(sum(value * value for value in dept_vector))

    # A vector whose values are all identical centres to all-zeros, so it has
    # no direction to compare and no cosine is defined. 0.0 is the honest
    # answer here, not a divide-by-zero guard: a flat profile carries no
    # signal about fit. It happens for real at session start (every trait at
    # the 0.5 prior) and when a student answers 3 to everything. Every
    # department then scores 0.0, ties, and softmax returns a uniform 1/15 —
    # far better than the old unnormalised sum, which confidently named
    # Workshops at 13.95% on the strength of its weights alone.
    if user_norm == 0.0 or dept_norm == 0.0:
        return 0.0

    dot = sum(u * d for u, d in zip(user_vector, dept_vector))
    return dot / (user_norm * dept_norm)


def softmax(scores: dict[str, float], temperature: float = 1.0) -> dict[str, float]:
    """Numerically stable softmax over a {key: score} mapping.

    `temperature` divides the scores before exponentiating: lower values
    sharpen the distribution, higher values flatten it. Subtracting the max
    first keeps exp() in range whatever the temperature.
    """
    max_score = max(scores.values())
    exp_scores = {
        key: math.exp((score - max_score) / temperature) for key, score in scores.items()
    }
    total = sum(exp_scores.values())
    return {key: value / total for key, value in exp_scores.items()}
