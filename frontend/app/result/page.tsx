"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ResultSummary } from "@/components/ResultSummary";
import { listDepartments } from "@/lib/api";
import { C, FONT } from "@/lib/theme";
import type { Department, Result } from "@/types/api";

const RESULT_STORAGE_KEY = "taqneeq_last_result";

export default function ResultPage() {
  const [result, setResult] = useState<Result | null>(null);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    const raw = sessionStorage.getItem(RESULT_STORAGE_KEY);
    if (!raw) {
      setNotFound(true);
      return;
    }
    setResult(JSON.parse(raw));
    // The result payload carries department ids and names but not their
    // descriptions, which the cards show — fetch them alongside.
    listDepartments()
      .then(setDepartments)
      .catch(() => setDepartments([]));
  }, []);

  if (notFound) {
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 20,
          padding: "96px 20px",
          textAlign: "center",
        }}
      >
        <span
          style={{
            font: `700 11px/1 ${FONT.mono}`,
            letterSpacing: ".22em",
            color: C.muted,
          }}
        >
          NO RESULT SAVED
        </span>
        <p style={{ color: C.text, maxWidth: "40ch", margin: 0 }}>
          There&apos;s no finished quiz in this browser session. Take the quiz and your result will
          appear here.
        </p>
        <Link
          href="/quiz"
          className="tq-btn-primary"
          style={{ fontSize: 16, padding: "15px 24px", textDecoration: "none" }}
        >
          Start the quiz →
        </Link>
      </div>
    );
  }

  if (!result) return null;

  return <ResultSummary result={result} departments={departments} />;
}
