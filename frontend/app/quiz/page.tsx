"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, startClassification, submitAnswer } from "@/lib/api";
import { ProgressBar } from "@/components/ProgressBar";
import { QuestionCard } from "@/components/QuestionCard";
import { C, FONT } from "@/lib/theme";
import type { Question } from "@/types/api";

const RESULT_STORAGE_KEY = "taqneeq_last_result";
const FADE_MS = 180;

function prefersReducedMotion(): boolean {
  return typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export default function QuizPage() {
  const router = useRouter();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [question, setQuestion] = useState<Question | null>(null);
  const [questionNumber, setQuestionNumber] = useState(1);
  const [maxQuestions, setMaxQuestions] = useState(15);
  const [selected, setSelected] = useState<number | null>(null);
  const [fadedOut, setFadedOut] = useState(false);
  const [loading, setLoading] = useState(true);
  const [locked, setLocked] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const begin = useCallback(async () => {
    setLoading(true);
    setError(null);
    setSelected(null);
    setFadedOut(false);
    setLocked(false);
    try {
      const start = await startClassification();
      setSessionId(start.session_id);
      setQuestion(start.question);
      setQuestionNumber(start.question_number);
      setMaxQuestions(start.total_max_questions);
      sessionStorage.setItem("taqneeq_session_id", start.session_id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong starting the quiz.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    begin();
  }, [begin]);

  /**
   * Picking an option submits immediately — the design has no separate
   * Continue button. The card fades out while the request is in flight, so
   * the wait reads as a transition rather than a stall.
   */
  async function pick(value: number) {
    if (!sessionId || !question || locked) return;
    setSelected(value);
    setLocked(true);
    setError(null);

    const animate = !prefersReducedMotion();
    if (animate) setTimeout(() => setFadedOut(true), 60);

    try {
      const [response] = await Promise.all([
        submitAnswer(sessionId, question.id, value),
        new Promise((resolve) => setTimeout(resolve, animate ? FADE_MS : 0)),
      ]);

      if (response.completed && response.result) {
        sessionStorage.setItem(RESULT_STORAGE_KEY, JSON.stringify(response.result));
        router.push("/result");
        return;
      }
      if (response.question) {
        setQuestion(response.question);
        setQuestionNumber(response.question_number ?? questionNumber + 1);
        setMaxQuestions(response.total_max_questions ?? maxQuestions);
        setSelected(null);
        setFadedOut(false);
        setLocked(false);
      }
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Something went wrong submitting your answer.",
      );
      setFadedOut(false);
      setLocked(false);
    }
  }

  if (loading) {
    return (
      <div
        style={{
          padding: "96px 20px",
          textAlign: "center",
          font: `700 12px/1 ${FONT.mono}`,
          letterSpacing: ".2em",
          color: C.muted,
        }}
      >
        LOADING YOUR QUIZ…
      </div>
    );
  }

  if (error && !question) {
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 18,
          padding: "96px 20px",
          textAlign: "center",
        }}
      >
        <p style={{ color: C.cream, maxWidth: "40ch" }}>{error}</p>
        <button type="button" onClick={begin} className="tq-btn-primary" style={{ fontSize: 16, padding: "14px 22px" }}>
          Try again
        </button>
      </div>
    );
  }

  if (!question) return null;

  return (
    <div style={{ maxWidth: 640, margin: "0 auto", padding: "22px 16px 0" }}>
      <div style={{ marginBottom: 8 }}>
        <span style={{ font: `700 11px/1 ${FONT.mono}`, letterSpacing: ".2em", color: C.lilac }}>
          QUESTION {questionNumber} · UP TO {maxQuestions}
        </span>
      </div>

      <ProgressBar current={questionNumber} max={maxQuestions} />

      <div
        style={{
          opacity: fadedOut ? 0 : 1,
          transform: `translateY(${fadedOut ? "-10px" : "0"})`,
          transition: "opacity .18s ease, transform .18s ease",
        }}
      >
        <QuestionCard
          question={question}
          number={questionNumber}
          selected={selected}
          locked={locked}
          onSelect={pick}
        />
      </div>

      {error && (
        <p style={{ marginTop: 14, fontSize: 14, color: C.cream }}>{error}</p>
      )}

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 12,
          marginTop: 18,
        }}
      >
        {/* The API rejects re-answering a question, so there is no true
            "previous question" to go back to — this restarts instead, and
            says so rather than pretending. */}
        <button type="button" onClick={begin} className="tq-btn-ghost" style={{ padding: "11px 14px" }}>
          ← START OVER
        </button>
        <span
          style={{
            font: `700 10px/1 ${FONT.mono}`,
            letterSpacing: ".16em",
            color: C.muted,
          }}
        >
          PICK ONE TO CONTINUE
        </span>
      </div>
    </div>
  );
}
