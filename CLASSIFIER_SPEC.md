# Taqneeq Adaptive Department Classifier — Simplified Specification

## Departments
15 departments: Admin, Artist & Guest Management, Digital Creatives, Film & Media,
Hospitality, Informals, In-house Creatives, Logistics, Marketing, Outreach, Publicity,
Social Media & Content Writing, Technical Events, Technicals, Workshops.

## Classification
1. Start every session with 4 seed questions.
2. Every trait has a prior of 0.5.
3. For each answer (1–5), normalise to (answer-1)/4.
4. Each trait score is the weighted mean of the 0.5 prior and every normalised
   answer that touched that trait. Weights: 0.6 for the prior, 1.0 for an
   answer's primary trait, 0.5 for each of its secondary traits. A trait no
   question has touched therefore stays at exactly 0.5, and later answers never
   discount earlier ones (there is no learning rate and no recency decay).
5. Department score = cosine similarity between the mean-centred user trait
   vector and the mean-centred department weight vector. "Mean-centred" means
   subtracting the vector's own mean from each of its components, so what is
   compared is the *shape* of the two profiles — which traits stand out
   relative to the rest — not their overall magnitude.
   If either centred vector is all zeros (norm 0), the score is 0.0. This is
   the correct answer, not a fallback: it means the profile is flat and carries
   no signal, which happens at session start (all traits at the 0.5 prior) and
   when a student answers 3 to everything. Every department then ties and
   step 6 returns a uniform 1/15.
6. Convert department scores to probabilities with a softmax at a configurable
   temperature, default 0.05. Lower temperature = sharper probabilities and an
   earlier stop; higher = flatter probabilities and a longer quiz.
7. After the minimum of 14 total questions, stop if:
   - top probability >= 0.65, AND
   - top probability - second probability >= 0.15.
8. Otherwise continue until 15 questions maximum.
9. If maximum is reached, return the highest-scoring department.

### Why this changed
Steps 4–6 previously specified a learning-rate trait update (primary 0.4,
secondary 0.2) and an unnormalised dot product, `sum(user_trait *
department_trait_weight)`, for the department score. Measurements on simulated
students showed that combination does not classify:

- **86.6%** of simulated students were routed to **Workshops**, regardless of
  their answers. An unnormalised dot product rewards departments whose weight
  vector is large across many traits, and because every trait starts at the 0.5
  prior, those departments lead before a single question is answered by a margin
  the questions cannot close.
- **11 of 15 departments were unreachable** — no combination of answers could
  produce them as the recommendation.
- The stopping rule's **0.65** confidence threshold was **unreachable** (highest
  observed top probability: **21.3%**), so the early-stop branch never fired and
  every session ran to the then-12-question maximum.

Mean-centring removes the magnitude advantage, so departments compete on profile
shape; the temperature-scaled softmax makes the 0.65 threshold attainable so the
stopping rule can do its job.

### Why the question budget changed (steps 7–8)
The minimum was 8 and the maximum 12. Both were raised after measuring accuracy
rather than coverage: a student whose answers mirror a department's own weight
vector — the easiest case there is — was placed in that department only **73%**
of the time, across 300 runs (15 departments × 20 seeds).

The scoring was not at fault. The same student answering **all 45** questions is
placed correctly **14 of 15** times, and the single miss is Hospitality losing to
Artist & Guest Management by 0.892 to 0.900, two departments whose weight vectors
have a centred cosine of 0.908. What failed was the budget: with a temperature of
0.05 the softmax crosses 0.65 while most traits still sit at the 0.5 prior, so
sessions ended after ~9 questions on evidence that thin.

Accuracy against a forced budget, same 300 runs, **on the 45-question bank**:

| questions | correct department | in top 3 |
| --------- | ------------------ | -------- |
| 8         | 73%                | 99%      |
| 12        | 76%                | 99%      |
| 14–16     | 93%                | 100%     |
| 20        | 96%                | 100%     |

14/16 buys most of the available accuracy for four more questions. Note that the
stopping rule's confidence figure is **not** calibrated: across these runs a wrong
recommendation still reported 0.63 mean confidence. The rule governs quiz length;
it is not evidence the answer is right, and the result page must not present it
as such.

### The 15-question cap, and why the bank now works against it
**15 is a product ceiling, not a measured optimum.** Students disengage past it.
Accuracy keeps climbing with more questions — 22 would score 96% — so within the
cap the lever is a better-targeted question bank, never a longer quiz.

Ten questions (q46–q55) were added to bring every trait to at least three primary
questions; `communication` previously had none, despite every department being
scored on it. That looked like a structural defect, and as a data-integrity
matter it was. But measured at the cap it costs accuracy, because the traits it
covers are the ones that discriminate least.

Directed accuracy at 14/15, 300 runs (15 departments × 20 seeds):

| bank         | correct department | in top 3 | mean questions |
| ------------ | ------------------ | -------- | -------------- |
| 45 questions | **94.7%**          | 100%     | 14.3           |
| 55 questions | **85.0%**          | 100%     | 14.4           |

The cause is mean-centring. A trait every department weights similarly is nearly
flat once centred and cannot separate them however often it is asked. Ranked by
standard deviation of weight across the 15 departments, the traits q46–q55 target
sit near the bottom: `leadership` 0.152, `event_energy` 0.200, `problem_solving`
0.211, `communication` 0.228. The discriminating traits are `visual_creativity`
0.322, `technical_ability` 0.305, `content_creativity` 0.294.

That interacts badly with `UNCOVERED_TRAIT_BONUS` (+3 for an untested trait),
which is blind to discriminative power. With 15 traits and 15 questions, that
bonus effectively forces one question per trait — so three `communication`
questions displace three that would have separated departments.

**Consequently: do not add questions for a trait merely because it has few.**
Weight the decision by how much that trait varies across departments. The right
fix for the current gap is questions that separate specific confusable pairs —
Technical Events versus Technicals (centred cosine 0.912) is half the remaining
error — or making the uncovered-trait bonus proportional to trait variance.

Two cautions. The accuracy curve is not monotonic across budgets (on the
55-question bank, 20 questions scored below 16), so a few points either way is
noise. And within the cap, minimums of 12, 13 and 14 all score within 0.3 points
of each other; 12/15 reaches the same accuracy with a mean of 13.2 questions
rather than 14.4, so the minimum can be lowered to shorten the average quiz at
no measured cost.

### Scope of this change: cosine similarity
Cosine similarity was previously barred from classification and permitted only
for `GET /departments/{id}/similar`. That bar is lifted for classification, as
specified in step 5, and **only** for classification.

`GET /departments/{id}/similar` is **unaffected** by this change. It continues to
compare *raw, uncentred* department weight vectors with plain cosine similarity,
as before. It is a browsing aid, not a classifier: it must not adopt the
mean-centring in step 5, must not apply a softmax, and its output must not feed
back into classification.

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
