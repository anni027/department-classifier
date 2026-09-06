import random

from app.core.classifier import select_next_question
from app.core.models import Department, Question


def make_question(qid, primary_trait, distinguishes=None):
    return Question(
        id=qid,
        text=f"question {qid}",
        primary_trait=primary_trait,
        secondary_traits=[],
        options=[],
        distinguishes=distinguishes or [],
    )


def make_department(dept_id, **weights):
    return Department(id=dept_id, name=dept_id, description="", weights=weights)


def test_uncovered_trait_bonus_wins_tie():
    dept1 = make_department("d1", trait_a=0.5, trait_b=0.5)
    dept2 = make_department("d2", trait_a=0.5, trait_b=0.5)
    departments_by_id = {"d1": dept1, "d2": dept2}
    q_covered = make_question("q_covered", "trait_a")
    q_uncovered = make_question("q_uncovered", "trait_b")

    chosen = select_next_question(
        [q_covered, q_uncovered],
        asked_primary_traits={"trait_a"},
        top2_dept_ids=("d1", "d2"),
        departments_by_id=departments_by_id,
        rng=random.Random(0),
    )
    assert chosen.id == "q_uncovered"


def test_top1_relevance_outranks_top2():
    dept1 = make_department("d1", strong=1.0, weak=0.0)
    dept2 = make_department("d2", strong=0.0, weak=1.0)
    departments_by_id = {"d1": dept1, "d2": dept2}
    q_for_top1 = make_question("q1", "strong")
    q_for_top2 = make_question("q2", "weak")

    chosen = select_next_question(
        [q_for_top1, q_for_top2],
        asked_primary_traits={"strong", "weak"},  # neutralise coverage bonus
        top2_dept_ids=("d1", "d2"),
        departments_by_id=departments_by_id,
        rng=random.Random(0),
    )
    assert chosen.id == "q1"


def test_relevance_scales_continuously_not_a_cliff():
    dept1 = make_department("d1", high=0.9, low=0.5)
    dept2 = make_department("d2", high=0.1, low=0.1)
    departments_by_id = {"d1": dept1, "d2": dept2}
    q_high = make_question("q_high", "high")
    q_low = make_question("q_low", "low")

    chosen = select_next_question(
        [q_high, q_low],
        asked_primary_traits={"high", "low"},
        top2_dept_ids=("d1", "d2"),
        departments_by_id=departments_by_id,
        rng=random.Random(0),
    )
    # weight 0.9 (well above any cliff) beats weight 0.5, proportionally, not via a threshold
    assert chosen.id == "q_high"


def test_distinguishes_bonus_requires_both_top_two():
    dept1 = make_department("d1", trait_a=0.5)
    dept2 = make_department("d2", trait_a=0.5)
    departments_by_id = {"d1": dept1, "d2": dept2}
    q_distinguishes_both = make_question("q_both", "trait_a", distinguishes=["d1", "d2"])
    q_distinguishes_one = make_question("q_one", "trait_a", distinguishes=["d1"])

    chosen = select_next_question(
        [q_distinguishes_both, q_distinguishes_one],
        asked_primary_traits={"trait_a"},
        top2_dept_ids=("d1", "d2"),
        departments_by_id=departments_by_id,
        rng=random.Random(0),
    )
    assert chosen.id == "q_both"


def test_jitter_only_breaks_exact_ties_never_overturns_a_real_gap():
    dept1 = make_department("d1", strong=1.0, weak=0.0)
    dept2 = make_department("d2", strong=0.0, weak=0.0)
    departments_by_id = {"d1": dept1, "d2": dept2}
    q_clear_winner = make_question("q_winner", "strong")  # base score ~3.0
    q_clear_loser = make_question("q_loser", "weak")  # base score ~0.0
    # jitter is capped at 0.05, far smaller than the 3.0 gap above, across many seeds
    for seed in range(50):
        chosen = select_next_question(
            [q_clear_winner, q_clear_loser],
            asked_primary_traits={"strong", "weak"},
            top2_dept_ids=("d1", "d2"),
            departments_by_id=departments_by_id,
            rng=random.Random(seed),
        )
        assert chosen.id == "q_winner"


def test_jitter_varies_the_pick_when_base_scores_are_tied():
    dept1 = make_department("d1", t=0.5)
    dept2 = make_department("d2", t=0.5)
    departments_by_id = {"d1": dept1, "d2": dept2}
    q_a = make_question("q_a", "t")
    q_b = make_question("q_b", "t")
    picks = {
        select_next_question(
            [q_a, q_b],
            asked_primary_traits={"t"},
            top2_dept_ids=("d1", "d2"),
            departments_by_id=departments_by_id,
            rng=random.Random(seed),
        ).id
        for seed in range(30)
    }
    # with identical base scores, jitter alone decides the winner -> both ids should appear
    assert picks == {"q_a", "q_b"}
