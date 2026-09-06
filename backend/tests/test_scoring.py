import pytest

from app.core.models import Department, Option, Question
from app.core.scoring import (
    PRIOR_WEIGHT,
    SECONDARY_WEIGHT,
    TEMPERATURE,
    compute_trait_scores,
    department_affinity,
    normalize_answer,
    softmax,
)

TRAITS = ["technical_ability", "problem_solving", "communication"]


def _question(question_id: str, primary: str, secondary: list[str] | None = None) -> Question:
    return Question(
        id=question_id,
        text="",
        primary_trait=primary,
        secondary_traits=secondary or [],
        options=[Option(value=v, label="") for v in range(1, 6)],
        distinguishes=[],
    )


@pytest.mark.parametrize(
    "value,expected",
    [(1, 0.0), (2, 0.25), (3, 0.5), (4, 0.75), (5, 1.0)],
)
def test_normalize_answer(value, expected):
    assert normalize_answer(value) == pytest.approx(expected)


def test_compute_trait_scores_primary_weight():
    questions_by_id = {"q1": _question("q1", "technical_ability")}
    scores = compute_trait_scores({"q1": 5}, questions_by_id, TRAITS)
    # (0.5*0.6 + 1.0*1.0) / (0.6 + 1.0) = 1.3/1.6 = 0.8125
    assert scores["technical_ability"] == pytest.approx(0.8125)
    # Untouched traits keep the prior exactly.
    assert scores["problem_solving"] == pytest.approx(0.5)
    assert scores["communication"] == pytest.approx(0.5)


def test_compute_trait_scores_secondary_weight():
    questions_by_id = {"q1": _question("q1", "technical_ability", ["problem_solving"])}
    scores = compute_trait_scores({"q1": 5}, questions_by_id, TRAITS)
    # secondary: (0.5*0.6 + 1.0*0.5) / (0.6 + 0.5) = 0.8/1.1
    expected = (0.5 * PRIOR_WEIGHT + 1.0 * SECONDARY_WEIGHT) / (PRIOR_WEIGHT + SECONDARY_WEIGHT)
    assert scores["problem_solving"] == pytest.approx(expected)
    assert scores["problem_solving"] == pytest.approx(0.8 / 1.1)
    # A secondary trait moves less far from the prior than the primary does,
    # which is the 2:1 ratio the old learning rates encoded.
    assert scores["problem_solving"] < scores["technical_ability"]


@pytest.mark.parametrize("answer_value", [1, 3, 5])
def test_compute_trait_scores_answers_1_3_5(answer_value):
    questions_by_id = {"q1": _question("q1", "communication")}
    scores = compute_trait_scores({"q1": answer_value}, questions_by_id, TRAITS)
    normalized = normalize_answer(answer_value)
    expected = (0.5 * PRIOR_WEIGHT + normalized * 1.0) / (PRIOR_WEIGHT + 1.0)
    assert scores["communication"] == pytest.approx(expected)


def test_compute_trait_scores_bounded_0_1():
    """A weighted mean of values in [0, 1] cannot leave [0, 1], so no
    clamping is needed even when every answer is maximal.
    """
    questions_by_id = {f"q{i}": _question(f"q{i}", "communication") for i in range(20)}
    responses = {f"q{i}": 5 for i in range(20)}
    scores = compute_trait_scores(responses, questions_by_id, TRAITS)
    assert 0.0 <= scores["communication"] <= 1.0
    assert scores["communication"] > 0.9  # 20 maximal answers swamp the prior


def test_compute_trait_scores_is_order_independent():
    """Same answers, different arrival orders -> identical trait vector.

    Guards the property the incremental learning-rate update did not have:
    under that scheme later answers counted for more, and reordering the
    same twelve answers changed the recommendation 52.7% of the time.
    """
    questions_by_id = {
        "q1": _question("q1", "technical_ability", ["problem_solving"]),
        "q2": _question("q2", "problem_solving", ["communication"]),
        "q3": _question("q3", "communication"),
        "q4": _question("q4", "technical_ability"),
    }
    answers = {"q1": 5, "q2": 1, "q3": 4, "q4": 2}

    orders = [
        ["q1", "q2", "q3", "q4"],
        ["q4", "q3", "q2", "q1"],
        ["q2", "q4", "q1", "q3"],
        ["q3", "q1", "q4", "q2"],
    ]
    vectors = [
        compute_trait_scores({qid: answers[qid] for qid in order}, questions_by_id, TRAITS)
        for order in orders
    ]

    first = vectors[0]
    assert all(vector == first for vector in vectors[1:])
    # Not a vacuous pass: the answers actually moved the traits off the prior.
    assert first != {trait: 0.5 for trait in TRAITS}


def test_compute_trait_scores_no_responses_returns_prior():
    assert compute_trait_scores({}, {}, TRAITS) == {trait: 0.5 for trait in TRAITS}


def test_department_affinity_known_combination():
    # Centred weights: [+0.5, 0.0, -0.5]. Cosine against a trait vector with
    # the same shape is +1, against the mirrored shape -1, against an
    # orthogonal shape 0. Three traits minimum: 1- and 2-trait vectors are
    # degenerate under centring.
    dept = Department(id="x", name="X", description="", weights={"a": 1.0, "b": 0.5, "c": 0.0})

    same_shape = {"a": 0.9, "b": 0.5, "c": 0.1}  # centred [+0.4, 0.0, -0.4]
    mirrored = {"a": 0.1, "b": 0.5, "c": 0.9}  # centred [-0.4, 0.0, +0.4]
    orthogonal = {"a": 0.25, "b": 1.0, "c": 0.25}  # centred [-0.25, +0.5, -0.25]

    assert department_affinity(same_shape, dept) == pytest.approx(1.0)
    assert department_affinity(mirrored, dept) == pytest.approx(-1.0)
    assert department_affinity(orthogonal, dept) == pytest.approx(0.0)


def test_department_affinity_ranks_sensibly():
    tech = Department(
        id="tech",
        name="Tech",
        description="",
        weights={"technical_ability": 1.0, "communication": 0.3, "public_speaking": 0.1},
    )
    outreach = Department(
        id="outreach",
        name="Outreach",
        description="",
        weights={"technical_ability": 0.1, "communication": 0.9, "public_speaking": 1.0},
    )
    builder = {"technical_ability": 0.9, "communication": 0.4, "public_speaking": 0.2}

    assert department_affinity(builder, tech) > department_affinity(builder, outreach)


def test_uniform_trait_vector_gives_zero_affinity_for_every_department(departments):
    """No signal -> no preference. A flat trait vector (session start, or a
    student who answers 3 to everything) centres to all-zeros, so every real
    department scores 0.0 and softmax hands back a uniform 1/15.
    """
    traits = list(departments[0].weights)
    uniform = {trait: 0.5 for trait in traits}

    assert all(department_affinity(uniform, dept) == 0.0 for dept in departments)

    probabilities = softmax({d.id: department_affinity(uniform, d) for d in departments}, TEMPERATURE)
    assert all(prob == pytest.approx(1 / len(departments)) for prob in probabilities.values())


def test_softmax_sums_to_one():
    probs = softmax({"a": 2.0, "b": 1.0, "c": 0.5, "d": -1.0})
    assert sum(probs.values()) == pytest.approx(1.0)


def test_softmax_stable_for_large_scores():
    probs = softmax({"a": 1000.0, "b": 999.0})
    assert sum(probs.values()) == pytest.approx(1.0)
    assert probs["a"] > probs["b"]


def test_softmax_higher_score_wins():
    probs = softmax({"a": 5.0, "b": 1.0})
    assert probs["a"] > probs["b"]


def test_softmax_low_temperature_is_more_peaked():
    scores = {"a": 0.9, "b": 0.6, "c": 0.3, "d": 0.0}

    default_temp = softmax(scores)
    low_temp = softmax(scores, temperature=TEMPERATURE)

    assert low_temp["a"] > default_temp["a"]
    assert low_temp["d"] < default_temp["d"]
    assert sum(low_temp.values()) == pytest.approx(1.0)
    # Raw affinity gaps this size are unreachable at temperature 1.0 (top
    # probability ~0.42); at 0.05 they clear the 0.65 stopping threshold.
    assert default_temp["a"] < 0.65 < low_temp["a"]


def test_softmax_stable_at_low_temperature_for_large_gaps():
    """(score - max) / 0.05 blows up fast; the max-subtraction must keep
    exp() in range rather than overflowing.
    """
    probs = softmax({"a": 500.0, "b": -500.0}, temperature=TEMPERATURE)
    assert sum(probs.values()) == pytest.approx(1.0)
    assert probs["a"] == pytest.approx(1.0)
