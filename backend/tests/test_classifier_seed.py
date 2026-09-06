import random

from app.core.classifier import SEED_QUESTION_IDS, get_seed_questions


def test_seed_questions_are_q01_to_q04(questions):
    seeds = get_seed_questions(questions)
    assert [q.id for q in seeds] == ["q01", "q02", "q03", "q04"]


def test_seed_questions_independent_of_input_order(questions):
    shuffled = list(questions)
    random.Random(42).shuffle(shuffled)
    seeds = get_seed_questions(shuffled)
    assert [q.id for q in seeds] == SEED_QUESTION_IDS
