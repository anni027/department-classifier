import random
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_departments, get_questions, get_repository, get_traits
from app.api.schemas import (
    AnswerRequest,
    AnswerResponse,
    DepartmentMatch,
    ExplanationOut,
    OptionOut,
    QuestionOut,
    ResultOut,
    StartResponse,
    StatusResponse,
    TraitScore,
)
from app.core.classifier import (
    MAXIMUM_QUESTIONS,
    build_explanation,
    calculate_probabilities,
    check_stopping,
    get_seed_questions,
    mark_question_served,
    record_answer,
    select_next_question,
    top_traits,
    top_two_departments,
)
from app.core.models import ClassifierState, Department, Question
from app.db.repository import SessionRecord, SessionRepository

router = APIRouter(prefix="/classification", tags=["classification"])


def _question_out(question: Question) -> QuestionOut:
    return QuestionOut(
        id=question.id,
        text=question.text,
        options=[OptionOut(value=o.value, label=o.label) for o in question.options],
    )


def _get_record_or_404(repo: SessionRepository, session_id) -> SessionRecord:
    record = repo.get(session_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown session id: {session_id}")
    return record


@router.post("/start", response_model=StartResponse, status_code=201)
def start_classification(
    departments: list[Department] = Depends(get_departments),
    questions: list[Question] = Depends(get_questions),
    traits: list[str] = Depends(get_traits),
    repo: SessionRepository = Depends(get_repository),
) -> StartResponse:
    trait_scores = {trait: 0.5 for trait in traits}
    record = repo.create(trait_scores)

    first_question = get_seed_questions(questions)[0]
    questions_asked = [*record.questions_asked, first_question.id]
    repo.update(record.id, questions_asked=questions_asked)

    return StartResponse(
        session_id=record.id,
        question=_question_out(first_question),
        question_number=1,
        total_max_questions=MAXIMUM_QUESTIONS,
    )


@router.post("/answer", response_model=AnswerResponse)
def submit_answer(
    body: AnswerRequest,
    departments: list[Department] = Depends(get_departments),
    questions: list[Question] = Depends(get_questions),
    traits: list[str] = Depends(get_traits),
    repo: SessionRepository = Depends(get_repository),
) -> AnswerResponse:
    record = _get_record_or_404(repo, body.session_id)
    if record.completed:
        raise HTTPException(status_code=409, detail="Session is already completed")
    if body.question_id not in record.questions_asked:
        raise HTTPException(status_code=400, detail=f"Question '{body.question_id}' was not served in this session")
    if body.question_id in record.responses:
        raise HTTPException(status_code=400, detail=f"Question '{body.question_id}' has already been answered")

    questions_by_id = {q.id: q for q in questions}
    departments_by_id = {d.id: d for d in departments}
    question = questions_by_id[body.question_id]

    state = ClassifierState(
        trait_scores=record.trait_scores,
        questions_asked=record.questions_asked,
        responses=record.responses,
    )
    state = record_answer(state, question, body.response, questions_by_id, traits)
    probabilities = calculate_probabilities(state.trait_scores, departments)
    questions_answered = len(state.responses)

    if check_stopping(probabilities, questions_answered):
        top_id, second_id = top_two_departments(probabilities)
        recommended = departments_by_id[top_id]
        runner_up = departments_by_id[second_id]
        explanation = build_explanation(recommended, state.trait_scores)

        repo.update(
            record.id,
            questions_asked=state.questions_asked,
            responses=state.responses,
            trait_scores=state.trait_scores,
            probabilities=probabilities,
            completed=True,
            recommended_department=recommended.id,
        )

        ranked = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)[:3]
        top_matches = [
            DepartmentMatch(id=dept_id, name=departments_by_id[dept_id].name, probability=prob)
            for dept_id, prob in ranked
        ]

        result = ResultOut(
            recommended_department=DepartmentMatch(
                id=recommended.id, name=recommended.name, probability=probabilities[top_id]
            ),
            runner_up=DepartmentMatch(id=runner_up.id, name=runner_up.name, probability=probabilities[second_id]),
            top_matches=top_matches,
            probabilities=probabilities,
            top_traits=[TraitScore(trait=t, score=s) for t, s in top_traits(state.trait_scores)],
            explanation=ExplanationOut(**explanation),
        )
        return AnswerResponse(completed=True, result=result)

    unanswered = [q for q in questions if q.id not in state.questions_asked]
    asked_primary_traits = {questions_by_id[qid].primary_trait for qid in state.questions_asked}
    top2_ids = top_two_departments(probabilities)
    # Seed the tie-break jitter from the session id, not the clock: the same
    # session then always asks the same questions, so a student reporting a
    # strange result can have it replayed exactly. Re-derived per request
    # rather than held in memory, so it survives restarts and any worker
    # handling the request.
    rng = random.Random(record.id.int)
    next_question = select_next_question(
        unanswered, asked_primary_traits, top2_ids, departments_by_id, rng
    )
    state = mark_question_served(state, next_question)

    repo.update(
        record.id,
        questions_asked=state.questions_asked,
        responses=state.responses,
        trait_scores=state.trait_scores,
        probabilities=probabilities,
    )

    return AnswerResponse(
        completed=False,
        question=_question_out(next_question),
        question_number=len(state.questions_asked),
        total_max_questions=MAXIMUM_QUESTIONS,
    )


@router.get("/status/{session_id}", response_model=StatusResponse)
def get_status(session_id: UUID, repo: SessionRepository = Depends(get_repository)) -> StatusResponse:
    record = _get_record_or_404(repo, session_id)
    questions_answered = len(record.responses)
    current_top_department = None
    current_probability = None
    if record.probabilities:
        current_top_department = max(record.probabilities, key=record.probabilities.get)
        current_probability = record.probabilities[current_top_department]

    return StatusResponse(
        session_id=record.id,
        questions_answered=questions_answered,
        max_questions=MAXIMUM_QUESTIONS,
        current_top_department=current_top_department,
        current_probability=current_probability,
        completed=record.completed,
        progress_percentage=round(questions_answered / MAXIMUM_QUESTIONS * 100, 1),
    )
