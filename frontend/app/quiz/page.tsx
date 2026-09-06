"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, startClassification, submitAnswer } from "@/lib/api";
import { ProgressBar } from "@/components/ProgressBar";
import { QuestionCard } from "@/components/QuestionCard";
import type { Question } from "@/types/api";

const RESULT_STORAGE_KEY = "taqneeq_last_result";

export default function QuizPage() {
  const router = useRouter();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [question, setQuestion] = useState<Question | null>(null);
  const [questionNumber, setQuestionNumber] = useState(1);
  const [maxQuestions, setMaxQuestions] = useState(12);
  const [selected, setSelected] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const begin = useCallback(async () => {
    setLoading(true);
    setError(null);
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

  async function handleContinue() {
    if (!sessionId || !question || selected === null) return;
    setSubmitting(true);
    setError(null);
    try {
      const response = await submitAnswer(sessionId, question.id, selected);
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
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong submitting your answer.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return <div className="py-24 text-center text-white/60">Loading your quiz...</div>;
  }

  if (error && !question) {
    return (
      <div className="flex flex-col items-center gap-4 py-24 text-center">
        <p className="text-red-300">{error}</p>
        <button onClick={begin} className="rounded-full bg-taqneeq-violet px-6 py-2 text-white">
          Try again
        </button>
      </div>
    );
  }

  if (!question) return null;

  return (
    <div className="flex flex-col gap-6">
      <ProgressBar current={questionNumber} max={maxQuestions} />
      <QuestionCard question={question} selected={selected} onSelect={setSelected} />
      {error && <p className="text-sm text-red-300">{error}</p>}
      <button
        onClick={handleContinue}
        disabled={selected === null || submitting}
        className="self-end rounded-full bg-taqneeq-violet px-8 py-3 font-semibold text-white transition-opacity disabled:cursor-not-allowed disabled:opacity-40"
      >
        {submitting ? "Saving..." : "Continue"}
      </button>
    </div>
  );
}
