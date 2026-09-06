"""Load and validate departments.json / questions.json.

Fails fast with a clear ValueError at startup rather than letting bad data
surface as a confusing error on the first request. Never mutates or
restructures the source files.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.core.classifier import SEED_QUESTION_IDS
from app.core.models import Department, Option, Question

# Every department must carry enough content to fill a result page.
MINIMUM_CONTENT_ENTRIES = 3


def load_departments(path: str | Path) -> list[Department]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        Department(
            id=d["id"],
            name=d["name"],
            description=d["description"],
            # .get, not [], so a file missing these fields is reported by
            # validate_data with a clear message instead of a raw KeyError.
            responsibilities=list(d.get("responsibilities", [])),
            skills=list(d.get("skills", [])),
            weights=d["weights"],
        )
        for d in raw["departments"]
    ]


def load_questions(path: str | Path) -> list[Question]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        Question(
            id=q["id"],
            text=q["text"],
            primary_trait=q["primary_trait"],
            secondary_traits=list(q["secondary_traits"]),
            options=[Option(value=o["value"], label=o["label"]) for o in q["options"]],
            distinguishes=list(q["distinguishes"]),
        )
        for q in raw["questions"]
    ]


def load_traits(questions_path: str | Path) -> list[str]:
    raw = json.loads(Path(questions_path).read_text(encoding="utf-8"))
    return list(raw["traits"])


def validate_data(
    departments: list[Department], questions: list[Question], traits: list[str]
) -> None:
    """Raise ValueError with a clear message on any structural inconsistency."""
    trait_set = set(traits)
    dept_ids = {d.id for d in departments}

    if not departments:
        raise ValueError("No departments loaded")
    if not questions:
        raise ValueError("No questions loaded")

    for dept in departments:
        missing = trait_set - dept.weights.keys()
        extra = dept.weights.keys() - trait_set
        if missing:
            raise ValueError(f"Department '{dept.id}' is missing weights for traits: {missing}")
        if extra:
            raise ValueError(f"Department '{dept.id}' has weights for unknown traits: {extra}")

        # The explanation shown to a student is these two lists verbatim, so
        # a department that is short of content produces a thin result page
        # rather than a crash — fail at startup instead.
        for field_name, entries in (
            ("responsibilities", dept.responsibilities),
            ("skills", dept.skills),
        ):
            if len(entries) < MINIMUM_CONTENT_ENTRIES:
                raise ValueError(
                    f"Department '{dept.id}' needs at least {MINIMUM_CONTENT_ENTRIES} "
                    f"{field_name} entries, found {len(entries)}"
                )

    seen_ids: set[str] = set()
    for q in questions:
        if q.id in seen_ids:
            raise ValueError(f"Duplicate question id: {q.id}")
        seen_ids.add(q.id)

        if q.primary_trait not in trait_set:
            raise ValueError(f"Question '{q.id}' has unknown primary_trait '{q.primary_trait}'")
        unknown_secondary = set(q.secondary_traits) - trait_set
        if unknown_secondary:
            raise ValueError(f"Question '{q.id}' has unknown secondary_traits: {unknown_secondary}")
        unknown_depts = set(q.distinguishes) - dept_ids
        if unknown_depts:
            raise ValueError(f"Question '{q.id}' distinguishes unknown department ids: {unknown_depts}")

    missing_seeds = set(SEED_QUESTION_IDS) - seen_ids
    if missing_seeds:
        raise ValueError(f"Seed question ids missing from question bank: {missing_seeds}")
