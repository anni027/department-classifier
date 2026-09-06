"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ResultSummary } from "@/components/ResultSummary";
import type { Result } from "@/types/api";

const RESULT_STORAGE_KEY = "taqneeq_last_result";

export default function ResultPage() {
  const [result, setResult] = useState<Result | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    const raw = sessionStorage.getItem(RESULT_STORAGE_KEY);
    if (!raw) {
      setNotFound(true);
      return;
    }
    setResult(JSON.parse(raw));
  }, []);

  if (notFound) {
    return (
      <div className="flex flex-col items-center gap-4 py-24 text-center">
        <p className="text-white/70">No result found. Take the quiz first.</p>
        <Link href="/quiz" className="rounded-full bg-taqneeq-violet px-6 py-2 text-white">
          Start the quiz
        </Link>
      </div>
    );
  }

  if (!result) return null;

  return <ResultSummary result={result} />;
}
