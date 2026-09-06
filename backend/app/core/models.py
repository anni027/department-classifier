"""Plain data structures for the classification engine.

Deliberately not Pydantic: this package must stay importable and testable
with zero FastAPI/DB knowledge. Pydantic validation belongs to the API layer
(app/api/schemas.py), which builds these from validated request data.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Option:
    value: int
    label: str


@dataclass(frozen=True)
class Question:
    id: str
    text: str
    primary_trait: str
    secondary_traits: list[str]
    options: list[Option]
    distinguishes: list[str]


@dataclass(frozen=True)
class Department:
    id: str
    name: str
    description: str
    weights: dict[str, float]


@dataclass
class ClassifierState:
    """Mutable-by-replacement session state the engine operates on.

    The engine never mutates in place; every update function returns a new
    dict/state so callers (API/DB layer) can persist the result explicitly.
    """

    trait_scores: dict[str, float]
    questions_asked: list[str] = field(default_factory=list)
    responses: dict[str, int] = field(default_factory=dict)
