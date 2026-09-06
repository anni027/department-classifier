import pytest

from app.core.models import Department
from app.core.scoring import department_score, normalize_answer, softmax, update_trait_scores


@pytest.mark.parametrize(
    "value,expected",
    [(1, 0.0), (2, 0.25), (3, 0.5), (4, 0.75), (5, 1.0)],
)
def test_normalize_answer(value, expected):
    assert normalize_answer(value) == pytest.approx(expected)


def test_update_trait_scores_primary_learning_rate():
    scores = {"technical_ability": 0.5, "problem_solving": 0.5}
    updated = update_trait_scores(scores, "technical_ability", [], answer_value=5)
    # new = 0.5*0.6 + 1.0*0.4 = 0.7
    assert updated["technical_ability"] == pytest.approx(0.7)
    assert updated["problem_solving"] == pytest.approx(0.5)  # untouched


def test_update_trait_scores_secondary_learning_rate():
    scores = {"technical_ability": 0.5, "problem_solving": 0.5}
    updated = update_trait_scores(scores, "technical_ability", ["problem_solving"], answer_value=5)
    # secondary lr = 0.4*0.5 = 0.2 -> new = 0.5*0.8 + 1.0*0.2 = 0.6
    assert updated["problem_solving"] == pytest.approx(0.6)


@pytest.mark.parametrize("answer_value", [1, 3, 5])
def test_update_trait_scores_answers_1_3_5(answer_value):
    scores = {"communication": 0.5}
    updated = update_trait_scores(scores, "communication", [], answer_value=answer_value)
    normalized = normalize_answer(answer_value)
    expected = 0.5 * 0.6 + normalized * 0.4
    assert updated["communication"] == pytest.approx(expected)


def test_update_trait_scores_bounded_0_1():
    scores = {"communication": 0.98}
    for _ in range(20):
        scores = update_trait_scores(scores, "communication", [], answer_value=5)
    assert 0.0 <= scores["communication"] <= 1.0


def test_department_score_known_combination():
    dept = Department(id="x", name="X", description="", weights={"a": 1.0, "b": 0.0})
    assert department_score({"a": 1.0, "b": 1.0}, dept) == pytest.approx(1.0)
    assert department_score({"a": 0.0, "b": 1.0}, dept) == pytest.approx(0.0)


def test_department_score_ranks_sensibly():
    high_match = Department(id="tech", name="Tech", description="", weights={"technical_ability": 1.0})
    low_match = Department(id="art", name="Art", description="", weights={"technical_ability": 0.1})
    trait_scores = {"technical_ability": 0.9}
    assert department_score(trait_scores, high_match) > department_score(trait_scores, low_match)


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
