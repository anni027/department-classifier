from fastapi import APIRouter, Depends

from app.api.deps import get_departments, get_questions
from app.api.schemas import HealthResponse
from app.core.models import Department, Question

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(
    departments: list[Department] = Depends(get_departments),
    questions: list[Question] = Depends(get_questions),
) -> HealthResponse:
    return HealthResponse(status="ok", departments_loaded=len(departments), questions_loaded=len(questions))
