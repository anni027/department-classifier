import random

import pytest

from app.core.classifier import simulate_session


def test_full_session_terminates_within_bounds_with_valid_department(departments, questions):
    state, probabilities = simulate_session(departments, questions, lambda _q: 5, random.Random(7))

    assert 8 <= len(state.questions_asked) <= 12
    dept_ids = {d.id for d in departments}
    top_dept_id = max(probabilities, key=probabilities.get)
    assert top_dept_id in dept_ids
    assert sum(probabilities.values()) == pytest.approx(1.0)


def test_full_session_never_repeats_a_question(departments, questions):
    state, _ = simulate_session(departments, questions, lambda _q: 1, random.Random(123))
    assert len(state.questions_asked) == len(set(state.questions_asked))


def test_full_session_hits_max_when_answers_stay_ambiguous(departments, questions):
    state, _ = simulate_session(departments, questions, lambda _q: 3, random.Random(99))
    assert len(state.questions_asked) <= 12
