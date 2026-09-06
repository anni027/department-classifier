"""Synthetic-persona sanity check for the classifier.

Not a pytest suite - a standalone script. Run with:
    python -m scripts.personas
from backend/. Prints each persona's recommended department for a human to
eyeball, plus loose (not exact-match) assertions on the obvious cases.
"""
import random
from pathlib import Path

from app.core.classifier import simulate_session
from app.core.data_loader import load_departments, load_questions

DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "data"

PERSONAS: dict[str, dict[str, list[str]]] = {
    # Each persona lists traits it's clearly HIGH and clearly LOW on. Traits
    # left unlisted stay neutral (answer=3). A persona that is only "high on
    # 2 traits, neutral on everything else" is unrealistic: a real student
    # who is not a people-person also rates communication/leadership-heavy
    # questions LOW, not neutral - and department_affinity compares centred
    # profiles, so a persona with almost no spread between its traits gives
    # the classifier very little shape to match on.
    "Technical Builder": {
        "high": ["technical_ability", "problem_solving", "execution"],
        "low": ["public_speaking", "negotiation", "people_skills", "leadership", "marketing_sense", "networking"],
    },
    "Digital Designer": {
        "high": ["visual_creativity", "content_creativity", "media_skills"],
        "low": ["negotiation", "public_speaking", "leadership", "people_skills", "networking"],
    },
    "Event Organiser": {
        "high": ["organisation", "execution", "leadership", "event_energy"],
        "low": ["visual_creativity", "media_skills", "technical_ability"],
    },
    "People Person": {
        "high": ["people_skills", "communication", "event_energy"],
        "low": ["technical_ability", "media_skills", "visual_creativity"],
    },
    "Marketing Strategist": {
        "high": ["marketing_sense", "content_creativity", "communication"],
        "low": ["technical_ability", "media_skills", "people_skills"],
    },
    "Networker": {
        "high": ["networking", "negotiation", "communication"],
        "low": ["technical_ability", "visual_creativity", "media_skills"],
    },
    "Content Creator": {
        "high": ["content_creativity", "communication", "marketing_sense"],
        "low": ["technical_ability", "negotiation", "leadership"],
    },
    "Media Creator": {
        "high": ["media_skills", "visual_creativity", "content_creativity"],
        "low": ["negotiation", "technical_ability", "leadership"],
    },
    "Logistics Planner": {
        "high": ["organisation", "execution", "problem_solving"],
        "low": ["visual_creativity", "media_skills", "public_speaking", "content_creativity"],
    },
    "Workshop/Partnership Person": {
        "high": ["negotiation", "networking", "public_speaking"],
        "low": ["technical_ability", "visual_creativity", "media_skills"],
    },
}


def make_answer_fn(high: list[str], low: list[str]):
    def answer_fn(question) -> int:
        if question.primary_trait in high:
            return 5
        if question.primary_trait in low:
            return 1
        return 3

    return answer_fn


def run_personas() -> dict[str, tuple[str, float]]:
    departments = load_departments(DATA_DIR / "departments.json")
    questions = load_questions(DATA_DIR / "questions.json")
    results = {}

    for name, traits in PERSONAS.items():
        answer_fn = make_answer_fn(traits["high"], traits["low"])
        state, probabilities = simulate_session(departments, questions, answer_fn, random.Random(42))
        top_dept_id = max(probabilities, key=probabilities.get)
        top_dept_name = next(d.name for d in departments if d.id == top_dept_id)
        results[name] = (top_dept_id, probabilities[top_dept_id])
        ranked = sorted(probabilities.items(), key=lambda kv: kv[1], reverse=True)[:3]
        ranked_str = ", ".join(f"{d}={p:.2f}" for d, p in ranked)
        print(f"{name:32s} -> {top_dept_name:32s} ({len(state.questions_asked)} q) top3: {ranked_str}")

    return results


def demo() -> None:
    results = run_personas()
    # Loose, directional checks only for personas with an unambiguous trait signature.
    assert results["Technical Builder"][0] in {"technicals", "technical_events"}
    assert results["Networker"][0] in {"outreach", "workshops"}
    assert results["Marketing Strategist"][0] in {"marketing", "publicity", "social_media_content"}
    print("\npersona sanity checks passed")


if __name__ == "__main__":
    demo()
