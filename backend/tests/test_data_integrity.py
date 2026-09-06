import pytest

from app.core.data_loader import validate_data


def test_real_data_is_valid(departments, questions, traits):
    validate_data(departments, questions, traits)  # must not raise


def test_15_departments(departments):
    assert len(departments) == 15


def test_45_questions(questions):
    assert len(questions) == 45


def test_every_department_has_all_traits(departments, traits):
    for dept in departments:
        assert set(dept.weights.keys()) == set(traits)


def test_department_missing_trait_raises(departments, questions, traits):
    broken = list(departments)
    bad = broken[0]
    stripped_weights = dict(bad.weights)
    del stripped_weights[traits[0]]
    broken[0] = type(bad)(id=bad.id, name=bad.name, description=bad.description, weights=stripped_weights)
    with pytest.raises(ValueError, match="missing weights"):
        validate_data(broken, questions, traits)


def test_question_unknown_trait_raises(departments, questions, traits):
    broken = list(questions)
    bad = broken[0]
    broken[0] = type(bad)(
        id=bad.id,
        text=bad.text,
        primary_trait="not_a_real_trait",
        secondary_traits=bad.secondary_traits,
        options=bad.options,
        distinguishes=bad.distinguishes,
    )
    with pytest.raises(ValueError, match="unknown primary_trait"):
        validate_data(departments, broken, traits)


def test_seed_questions_present(departments, questions, traits):
    ids = {q.id for q in questions}
    assert {"q01", "q02", "q03", "q04"}.issubset(ids)
