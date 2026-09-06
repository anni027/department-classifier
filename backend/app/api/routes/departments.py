import math

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_departments
from app.api.schemas import DepartmentDetailOut, DepartmentOut, SimilarDepartmentOut
from app.core.models import Department

router = APIRouter(prefix="/departments", tags=["departments"])

SIMILAR_LIMIT = 5


def _find(departments: list[Department], department_id: str) -> Department:
    for dept in departments:
        if dept.id == department_id:
            return dept
    raise HTTPException(status_code=404, detail=f"Unknown department id: {department_id}")


def _cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    """Plain-Python cosine similarity over RAW, uncentred trait-weight vectors.

    Not the same computation as classification's department_affinity(), which
    mean-centres both vectors first. This one is a browsing aid: it answers
    "which departments look like this one", so absolute weight magnitude is
    part of the answer. Keep it uncentred, keep it out of classification, and
    do not feed its output back into scoring. See CLASSIFIER_SPEC.md,
    "Scope of this change: cosine similarity".
    """
    dot = sum(a[trait] * b[trait] for trait in a)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


@router.get("", response_model=list[DepartmentOut])
def list_departments(departments: list[Department] = Depends(get_departments)) -> list[DepartmentOut]:
    return [DepartmentOut(id=d.id, name=d.name, description=d.description) for d in departments]


@router.get("/{department_id}", response_model=DepartmentDetailOut)
def get_department(
    department_id: str, departments: list[Department] = Depends(get_departments)
) -> DepartmentDetailOut:
    dept = _find(departments, department_id)
    return DepartmentDetailOut(
        id=dept.id,
        name=dept.name,
        description=dept.description,
        weights=dept.weights,
        responsibilities=dept.responsibilities,
        skills=dept.skills,
    )


@router.get("/{department_id}/similar", response_model=list[SimilarDepartmentOut])
def get_similar_departments(
    department_id: str, departments: list[Department] = Depends(get_departments)
) -> list[SimilarDepartmentOut]:
    target = _find(departments, department_id)
    scored = [
        SimilarDepartmentOut(id=d.id, name=d.name, similarity=_cosine_similarity(target.weights, d.weights))
        for d in departments
        if d.id != department_id
    ]
    scored.sort(key=lambda item: item.similarity, reverse=True)
    return scored[:SIMILAR_LIMIT]
