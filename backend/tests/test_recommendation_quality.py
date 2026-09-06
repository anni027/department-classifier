"""Behavioural tests: are the recommendations usable?

Every other test in this suite checks that the arithmetic matches the
specification. All of them passed against a classifier that sent 86.6% of
students to Workshops and could never produce 11 of the 15 departments,
because "computes what the spec says" and "gives a student a useful answer"
are different properties. These tests check the second one, at the level of
a whole simulated cohort rather than a single function.
"""
import random
from collections import Counter

import pytest

from app.core.classifier import calculate_probabilities, simulate_session
from app.core.scoring import compute_trait_scores
from scripts.personas import PERSONAS, make_answer_fn

# Large enough for 15 departments to show up and for the share of the most
# common one to be meaningful; small enough that the file runs in ~1s.
COHORT_SIZE = 300

MAX_DEPARTMENT_SHARE = 0.30

# Loose, directional expectations promoted from scripts/personas.py. Each set
# is deliberately wider than one department: the point is to catch collapse
# (everyone landing in the same place, or a clear technical persona landing in
# Hospitality), not to freeze today's exact output.
PERSONA_EXPECTATIONS: dict[str, set[str]] = {
    "Technical Builder": {"technicals", "technical_events"},
    "Digital Designer": {"digital_creatives", "in_house_creatives", "film_media"},
    "Event Organiser": {"admin", "logistics", "informals", "hospitality"},
    # Workshops belongs here: it weights communication 0.95 and people_skills
    # 0.80, and this persona is neutral on the negotiation/networking traits
    # that would separate it from Outreach. The persona genuinely does not
    # carry the information needed to pick between the people-facing
    # departments, and it lands on four different ones across seeds.
    "People Person": {"hospitality", "outreach", "informals", "artist_guest_management", "workshops"},
    "Marketing Strategist": {"marketing", "publicity", "social_media_content"},
    "Networker": {"outreach", "workshops", "marketing", "artist_guest_management"},
    "Content Creator": {"social_media_content", "publicity", "marketing", "in_house_creatives"},
    "Media Creator": {"film_media", "digital_creatives", "social_media_content", "in_house_creatives"},
    "Logistics Planner": {"logistics", "admin", "technicals"},
    "Workshop/Partnership Person": {"workshops", "outreach", "artist_guest_management"},
}


def _student_answer_fn(rng: random.Random, traits: list[str]):
    """Answer function for one randomised student.

    Students are given a few strong traits and a few weak ones rather than
    answering uniformly at random: a cohort of pure noise has no profile
    shape to classify, so it would test nothing about whether real students
    can reach a department.
    """
    shuffled = list(traits)
    rng.shuffle(shuffled)
    high = set(shuffled[:3])
    low = set(shuffled[3:6])

    def answer_fn(question) -> int:
        if question.primary_trait in high:
            return rng.choice([4, 5])
        if question.primary_trait in low:
            return rng.choice([1, 2])
        return rng.choice([2, 3, 4])

    return answer_fn


@pytest.fixture(scope="module")
def cohort(departments, questions):
    """Simulate COHORT_SIZE students once and share the outcome.

    Every RNG is seeded from the student index, so a failure here is
    reproducible rather than a flake to re-run until it passes.
    """
    traits = list(departments[0].weights)
    recommendations: list[str] = []
    served_questions: Counter[str] = Counter()

    for student in range(COHORT_SIZE):
        answer_fn = _student_answer_fn(random.Random(1000 + student), traits)
        state, probabilities = simulate_session(
            departments, questions, answer_fn, random.Random(student)
        )
        recommendations.append(max(probabilities, key=probabilities.get))
        served_questions.update(state.questions_asked)

    return recommendations, served_questions


def test_every_department_is_reachable(cohort, departments):
    """No department is unreachable. 11 of 15 were, before the scoring fix."""
    recommendations, _ = cohort
    recommended = set(recommendations)
    unreachable = {d.id for d in departments} - recommended

    assert not unreachable, (
        f"{len(unreachable)} of {len(departments)} departments were never recommended "
        f"across {COHORT_SIZE} students: {sorted(unreachable)}"
    )


def test_no_department_dominates(cohort):
    """No department takes more than 30% of a varied cohort.

    This is the test that would have caught the original failure on day one:
    the unnormalised dot product gave Workshops 86.6%.
    """
    recommendations, _ = cohort
    counts = Counter(recommendations)
    top_department, top_count = counts.most_common(1)[0]
    share = top_count / len(recommendations)

    assert share <= MAX_DEPARTMENT_SHARE, (
        f"{top_department} took {share:.1%} of {len(recommendations)} recommendations "
        f"(limit {MAX_DEPARTMENT_SHARE:.0%}); distribution: {counts.most_common()}"
    )


def test_question_order_does_not_change_the_result(departments, questions):
    """The same answers in any order recommend the same department.

    Selection order is inherently sequential, so this fixes the answered set
    and varies only the order it is folded into the trait vector — which is
    where the old learning-rate update lost order-independence.
    """
    traits = list(departments[0].weights)
    questions_by_id = {q.id: q for q in questions}

    answered = [q.id for q in questions[:12]]
    answers = {qid: 1 + index % 5 for index, qid in enumerate(answered)}

    shuffler = random.Random(99)
    orders = [answered, list(reversed(answered))]
    for _ in range(4):
        shuffled = list(answered)
        shuffler.shuffle(shuffled)
        orders.append(shuffled)

    recommendations = set()
    for order in orders:
        trait_scores = compute_trait_scores(
            {qid: answers[qid] for qid in order}, questions_by_id, traits
        )
        probabilities = calculate_probabilities(trait_scores, departments)
        recommendations.add(max(probabilities, key=probabilities.get))

    assert len(recommendations) == 1, f"order changed the recommendation: {recommendations}"


def test_no_question_is_permanently_unreachable(cohort, questions):
    """Every question in the bank reaches at least one student.

    12 of 45 were dead weight before the scoring fix: with the leaderboard
    frozen, question selection kept steering to the same traits.
    """
    _, served_questions = cohort
    never_served = {q.id for q in questions} - set(served_questions)

    assert not never_served, (
        f"{len(never_served)} of {len(questions)} questions were never served "
        f"across {COHORT_SIZE} students: {sorted(never_served)}"
    )


@pytest.mark.parametrize("persona_name", sorted(PERSONA_EXPECTATIONS))
def test_personas_land_sensibly(persona_name, departments, questions):
    """A student with an unambiguous profile lands somewhere defensible."""
    persona = PERSONAS[persona_name]
    answer_fn = make_answer_fn(persona["high"], persona["low"])

    _, probabilities = simulate_session(departments, questions, answer_fn, random.Random(42))
    recommended = max(probabilities, key=probabilities.get)

    assert recommended in PERSONA_EXPECTATIONS[persona_name], (
        f"{persona_name} (high: {persona['high']}) was recommended {recommended}, "
        f"expected one of {sorted(PERSONA_EXPECTATIONS[persona_name])}"
    )
