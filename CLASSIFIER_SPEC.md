# Taqneeq Adaptive Department Classifier — Simplified Specification

## Departments
15 departments: Admin, Artist & Guest Management, Digital Creatives, Film & Media,
Hospitality, Informals, In-house Creatives, Logistics, Marketing, Outreach, Publicity,
Social Media & Content Writing, Technical Events, Technicals, Workshops.

## Classification
1. Start every session with 4 seed questions.
2. Initialise every trait at 0.5.
3. For each answer (1–5), normalise to (answer-1)/4.
4. Update primary trait with learning rate 0.4:
   new = old*(1-0.4) + normalized_answer*0.4
5. Update each secondary trait with half the learning rate (0.2).
6. Department score = sum(user_trait * department_trait_weight).
7. Convert department scores to probabilities with softmax.
8. After the minimum of 8 total questions, stop if:
   - top probability >= 0.65, AND
   - top probability - second probability >= 0.15.
9. Otherwise continue until 12 questions maximum.
10. If maximum is reached, return the highest-scoring department.

## Adaptive question selection
Do NOT simulate five possible answers or calculate Shannon entropy.

For each unanswered question, calculate:
- +3 if it targets a trait strongly relevant to the current #1 department
- +2 if it targets a trait strongly relevant to the current #2 department
- +3 if its primary trait is currently weakly measured (few/no previous questions)
- +2 if it distinguishes the current top two departments
- + information_value if present
- small random jitter (0–0.05) only to break ties

Choose the highest-scoring question.

## Explanation
No RAG/FAISS/LangChain required.
Build the explanation from departments.json:
- recommended department description
- 3 strongest user traits relative to department
- 3 relevant responsibilities
- 3 skills/perks
- second-best department as an alternative

An LLM can be added later as an optional wording layer; classification must never depend on it.

## Session model
id
questions_asked
responses
trait_scores
probabilities
completed
recommended_department
created_at
updated_at

In-memory storage is acceptable for development. Use PostgreSQL for production.
