"""Adaptive classification engine: seed order, question selection, stopping
rule, and deterministic explanation generation.

Zero FastAPI/DB/HTTP imports. Everything here takes plain data in and
returns plain data out so it can be unit tested directly.
"""
from __future__ import annotations

import random
import re

from app.core.models import ClassifierState, Department, Question
from app.core.scoring import department_score, softmax, update_trait_scores

# Explicit, named seed-question designation — looked up by id, never derived
# from whatever position questions.json happens to list them in. See
# CLASSIFIER_SPEC.md section 13 ("the first four questions" = these four).
SEED_QUESTION_IDS: list[str] = ["q01", "q02", "q03", "q04"]

MINIMUM_QUESTIONS = 8
MAXIMUM_QUESTIONS = 12
STOP_TOP_PROBABILITY = 0.65
STOP_PROBABILITY_GAP = 0.15

# Bonus weights from CLASSIFIER_SPEC.md "Adaptive question selection".
TOP1_RELEVANCE_WEIGHT = 3
TOP2_RELEVANCE_WEIGHT = 2
UNCOVERED_TRAIT_BONUS = 3
DISTINGUISHES_BONUS = 2
JITTER_MAX = 0.05

TRAIT_LABELS: dict[str, str] = {
    "technical_ability": "Technical building",
    "problem_solving": "Problem solving",
    "visual_creativity": "Visual design",
    "content_creativity": "Content creation",
    "communication": "Communication",
    "public_speaking": "Public speaking",
    "leadership": "Leadership",
    "people_skills": "People skills",
    "organisation": "Organisation",
    "execution": "Execution",
    "negotiation": "Negotiation",
    "networking": "Networking",
    "marketing_sense": "Marketing strategy",
    "event_energy": "Event energy",
    "media_skills": "Media production",
}


def get_seed_questions(all_questions: list[Question]) -> list[Question]:
    """Return the four designated seed questions, in SEED_QUESTION_IDS order.

    Independent of the order `all_questions` was loaded in.
    """
    by_id = {q.id: q for q in all_questions}
    return [by_id[qid] for qid in SEED_QUESTION_IDS]


def mark_question_served(state: ClassifierState, question: Question) -> ClassifierState:
    """Return a NEW ClassifierState with `question` appended to questions_asked.

    Called when a question is handed to the client, BEFORE it is answered.
    This is what lets the API layer distinguish "wrong question" (id not in
    questions_asked) from "duplicate answer" (id already in responses).
    """
    return ClassifierState(
        trait_scores=dict(state.trait_scores),
        questions_asked=[*state.questions_asked, question.id],
        responses=dict(state.responses),
    )


def record_answer(state: ClassifierState, question: Question, answer_value: int) -> ClassifierState:
    """Return a NEW ClassifierState with the answer recorded and traits updated.

    Does not mutate `state`. Caller (API/DB layer) is responsible for
    persisting the returned state.
    """
    new_traits = update_trait_scores(
        state.trait_scores, question.primary_trait, question.secondary_traits, answer_value
    )
    new_responses = dict(state.responses)
    new_responses[question.id] = answer_value
    return ClassifierState(
        trait_scores=new_traits,
        questions_asked=list(state.questions_asked),
        responses=new_responses,
    )


def calculate_probabilities(
    trait_scores: dict[str, float], departments: list[Department]
) -> dict[str, float]:
    scores = {dept.id: department_score(trait_scores, dept) for dept in departments}
    return softmax(scores)


def top_two_departments(probabilities: dict[str, float]) -> tuple[str, str]:
    ranked = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
    return ranked[0][0], ranked[1][0]


def select_next_question(
    unanswered: list[Question],
    asked_primary_traits: set[str],
    top2_dept_ids: tuple[str, str],
    departments_by_id: dict[str, Department],
    rng: random.Random | None = None,
) -> Question:
    """Pick the highest-scoring unanswered question.

    candidate_score =
        TOP1_RELEVANCE_WEIGHT * dept1.weights[primary_trait]   (continuous, max +3)
      + TOP2_RELEVANCE_WEIGHT * dept2.weights[primary_trait]   (continuous, max +2)
      + UNCOVERED_TRAIT_BONUS if primary_trait not yet asked   (+3)
      + DISTINGUISHES_BONUS if distinguishes covers both top-2 depts (+2)
      + 0 for information_value (absent from every question in the data)
      + jitter in [0, JITTER_MAX) to break exact ties only
    """
    rng = rng or random.Random()
    dept1 = departments_by_id[top2_dept_ids[0]]
    dept2 = departments_by_id[top2_dept_ids[1]]
    top2_set = set(top2_dept_ids)

    def score(question: Question) -> float:
        total = TOP1_RELEVANCE_WEIGHT * dept1.weights[question.primary_trait]
        total += TOP2_RELEVANCE_WEIGHT * dept2.weights[question.primary_trait]
        if question.primary_trait not in asked_primary_traits:
            total += UNCOVERED_TRAIT_BONUS
        if top2_set.issubset(set(question.distinguishes)):
            total += DISTINGUISHES_BONUS
        total += rng.uniform(0, JITTER_MAX)
        return total

    return max(unanswered, key=score)


def check_stopping(
    probabilities: dict[str, float],
    questions_answered: int,
    minimum: int = MINIMUM_QUESTIONS,
    maximum: int = MAXIMUM_QUESTIONS,
) -> bool:
    if questions_answered >= maximum:
        return True
    if questions_answered < minimum:
        return False
    ranked = sorted(probabilities.values(), reverse=True)
    top, second = ranked[0], ranked[1]
    return top >= STOP_TOP_PROBABILITY and (top - second) >= STOP_PROBABILITY_GAP


def top_traits(trait_scores: dict[str, float], count: int = 3) -> list[tuple[str, float]]:
    return sorted(trait_scores.items(), key=lambda item: item[1], reverse=True)[:count]


_CLAUSE_SPLIT_RE = re.compile(r",| and ")


def _split_description_clauses(description: str) -> list[str]:
    text = description.rstrip(".")
    clauses = [clause.strip() for clause in _CLAUSE_SPLIT_RE.split(text)]
    return [clause[0].upper() + clause[1:] for clause in clauses if clause]


def simulate_session(
    departments: list[Department],
    questions: list[Question],
    answer_fn,
    rng: random.Random | None = None,
) -> tuple[ClassifierState, dict[str, float]]:
    """Drive the full classifier loop end-to-end with no HTTP/DB involved.

    `answer_fn(question) -> int` supplies a 1-5 answer for each question
    served. Used by tests and the persona sanity script — never by the API,
    which processes exactly one answer per request.
    """
    rng = rng or random.Random()
    departments_by_id = {d.id: d for d in departments}
    questions_by_id = {q.id: q for q in questions}

    state = ClassifierState(trait_scores={t: 0.5 for t in departments[0].weights})

    for question in get_seed_questions(questions):
        state = mark_question_served(state, question)
        state = record_answer(state, question, answer_fn(question))

    probabilities = calculate_probabilities(state.trait_scores, departments)

    while not check_stopping(probabilities, len(state.responses)):
        unanswered = [q for q in questions if q.id not in state.questions_asked]
        asked_primary_traits = {questions_by_id[qid].primary_trait for qid in state.questions_asked}
        top2 = top_two_departments(probabilities)
        next_question = select_next_question(unanswered, asked_primary_traits, top2, departments_by_id, rng)
        state = mark_question_served(state, next_question)
        state = record_answer(state, next_question, answer_fn(next_question))
        probabilities = calculate_probabilities(state.trait_scores, departments)

    return state, probabilities


def build_explanation(
    recommended: Department,
    trait_scores: dict[str, float],
    clause_count: int = 3,
    skill_count: int = 3,
) -> dict[str, list[str]]:
    """Deterministic explanation built only from `description` + trait scores.

    departments.json has no responsibilities/skills fields, so "what you'll
    do" comes from clause-splitting `description`, and "skills gained" comes
    from the traits most relevant to this department (score * weight),
    labelled via the static TRAIT_LABELS map.
    """
    what_youll_do = _split_description_clauses(recommended.description)[:clause_count]

    relevance_ranked = sorted(
        recommended.weights.keys(),
        key=lambda trait: trait_scores[trait] * recommended.weights[trait],
        reverse=True,
    )[:skill_count]

    return {
        "what_youll_do": what_youll_do,
        "skills_gained": [TRAIT_LABELS[trait] for trait in relevance_ranked],
        "strongest_traits": relevance_ranked,
    }
