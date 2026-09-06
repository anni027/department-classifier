from collections import Counter
from dataclasses import replace

import pytest

from app.core.data_loader import MINIMUM_CONTENT_ENTRIES, validate_data


def test_real_data_is_valid(departments, questions, traits):
    validate_data(departments, questions, traits)  # must not raise


def test_15_departments(departments):
    assert len(departments) == 15


def test_question_bank_size(questions):
    assert len(questions) == 55


def test_every_trait_has_at_least_three_primary_questions(questions, traits):
    """A trait no question targets directly is only ever moved at half weight,
    as somebody else's secondary — so it barely separates departments even
    though every department is scored on it. `communication` was primary for
    zero of the original 45 questions.

    The minimum is exactly 3 with no slack: adding a trait without questions
    for it fails here rather than quietly degrading the classifier.
    """
    counts = Counter(q.primary_trait for q in questions)
    thin = {trait: counts[trait] for trait in traits if counts[trait] < 3}
    assert not thin, f"traits with fewer than 3 primary questions: {thin}"


def test_every_department_has_all_traits(departments, traits):
    for dept in departments:
        assert set(dept.weights.keys()) == set(traits)


def test_department_missing_trait_raises(departments, questions, traits):
    broken = list(departments)
    stripped_weights = dict(broken[0].weights)
    del stripped_weights[traits[0]]
    broken[0] = replace(broken[0], weights=stripped_weights)
    with pytest.raises(ValueError, match="missing weights"):
        validate_data(broken, questions, traits)


def test_every_department_has_real_content(departments):
    for dept in departments:
        assert len(dept.responsibilities) >= MINIMUM_CONTENT_ENTRIES
        assert len(dept.skills) >= MINIMUM_CONTENT_ENTRIES
        assert all(entry.strip() for entry in dept.responsibilities + dept.skills)


@pytest.mark.parametrize("field_name", ["responsibilities", "skills"])
def test_department_thin_content_raises(departments, questions, traits, field_name):
    """A department short of content must fail at startup, not produce a
    half-empty result page for a student.
    """
    broken = list(departments)
    too_few = list(getattr(broken[0], field_name))[: MINIMUM_CONTENT_ENTRIES - 1]
    broken[0] = replace(broken[0], **{field_name: too_few})
    with pytest.raises(ValueError, match=f"at least {MINIMUM_CONTENT_ENTRIES} {field_name}"):
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


# Department pairs students genuinely get confused between. `distinguishes`
# feeds the +2 tie-break bonus in select_next_question(), so a pair listed
# here needs questions that separate it — otherwise the bonus does nothing in
# exactly the close calls it exists for.
CONFUSABLE_PAIRS = [
    ("technical_events", "technicals"),
    ("digital_creatives", "in_house_creatives"),
    ("digital_creatives", "film_media"),
    ("social_media_content", "marketing"),
    ("outreach", "workshops"),
    ("admin", "logistics"),
    ("hospitality", "artist_guest_management"),
    ("publicity", "marketing"),
    ("informals", "publicity"),
]

# Two, not one: a session that has already served the only distinguishing
# question gets no bonus from it a second time, so a pair with a single
# question has no spare.
MINIMUM_QUESTIONS_PER_PAIR = 2


def test_no_question_has_an_empty_distinguishes_list(questions):
    empty = [q.id for q in questions if not q.distinguishes]
    assert not empty, f"questions with no distinguishes entries: {empty}"


@pytest.mark.parametrize("pair", CONFUSABLE_PAIRS, ids=lambda p: f"{p[0]}_vs_{p[1]}")
def test_confusable_pairs_have_distinguishing_questions(questions, pair):
    covering = [q.id for q in questions if set(pair) <= set(q.distinguishes)]
    assert len(covering) >= MINIMUM_QUESTIONS_PER_PAIR, (
        f"{pair[0]} vs {pair[1]} is separated by {len(covering)} question(s) "
        f"({covering}); needs at least {MINIMUM_QUESTIONS_PER_PAIR}"
    )
