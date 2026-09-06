"""All API request/response Pydantic models in one file.

Fewer than 20 small models for one API surface doesn't justify a package.
"""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class OptionOut(BaseModel):
    value: int
    label: str


class QuestionOut(BaseModel):
    id: str
    text: str
    options: list[OptionOut]


class StartResponse(BaseModel):
    session_id: UUID
    question: QuestionOut
    question_number: int
    total_max_questions: int


class AnswerRequest(BaseModel):
    session_id: UUID
    question_id: str
    response: int = Field(ge=1, le=5)


class DepartmentMatch(BaseModel):
    id: str
    name: str
    probability: float


class TraitScore(BaseModel):
    trait: str
    score: float


class ExplanationOut(BaseModel):
    what_youll_do: list[str]
    skills_gained: list[str]
    strongest_traits: list[str]


class ResultOut(BaseModel):
    recommended_department: DepartmentMatch
    runner_up: DepartmentMatch
    top_matches: list[DepartmentMatch]
    probabilities: dict[str, float]
    top_traits: list[TraitScore]
    explanation: ExplanationOut


class AnswerResponse(BaseModel):
    completed: bool
    question: QuestionOut | None = None
    question_number: int | None = None
    total_max_questions: int | None = None
    result: ResultOut | None = None


class StatusResponse(BaseModel):
    session_id: UUID
    questions_answered: int
    max_questions: int
    current_top_department: str | None
    current_probability: float | None
    completed: bool
    progress_percentage: float


class DepartmentOut(BaseModel):
    id: str
    name: str
    description: str


class DepartmentDetailOut(DepartmentOut):
    weights: dict[str, float]
    responsibilities: list[str]
    skills: list[str]


class SimilarDepartmentOut(BaseModel):
    id: str
    name: str
    similarity: float


class HealthResponse(BaseModel):
    status: str
    departments_loaded: int
    questions_loaded: int
