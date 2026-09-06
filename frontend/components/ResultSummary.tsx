"use client";

import Link from "next/link";
import type { CSSProperties } from "react";
import {
  C,
  FONT,
  barFill,
  barTrack,
  creamPanel,
  darkPanel,
  diamond,
  monoLabel,
  purplePanel,
  traitLabel,
} from "@/lib/theme";
import type { Department, Result } from "@/types/api";

/**
 * Cut-offs for the qualitative match label.
 *
 * PRESENTATION ONLY. The underlying number is a softmax over department
 * scores, rescaled so the 15 departments sum to 1. It is not a probability of
 * anything observable: nobody has checked whether students shown a high score
 * actually join and stay at a higher rate than students shown a low one.
 * These thresholds exist so the page can say "strong" instead of "83%", which
 * would imply a precision the number does not have. Do not surface the raw
 * figure to students until it has been calibrated against real outcomes.
 */
const MATCH_STRENGTH_THRESHOLDS = { strong: 0.6, good: 0.35 } as const;

function matchStrengthLabel(probability: number): string {
  if (probability >= MATCH_STRENGTH_THRESHOLDS.strong) return "Strong match";
  if (probability >= MATCH_STRENGTH_THRESHOLDS.good) return "Good match";
  return "Possible match";
}

/**
 * How close two scores have to be before we treat them as indistinguishable.
 * Also presentation only — a display decision, not a statistical test.
 */
const TIE_EPSILON = 0.01;

/**
 * True when the answers did not point anywhere in particular.
 *
 * A student who answers neutrally throughout produces a flat trait vector,
 * which scores 0 against every department and comes back as an exact 1/15
 * tie. Naming a "winner" out of that is fiction, so the page says so instead.
 * Also catches a top two that are effectively level, where the ordering is
 * noise rather than a finding.
 */
function hasNoClearSignal(result: Result): boolean {
  const departmentCount = Object.keys(result.probabilities).length;
  if (departmentCount === 0) return false;

  const uniform = 1 / departmentCount;
  const top = result.recommended_department.probability;
  const second = result.runner_up.probability;

  return Math.abs(top - uniform) < TIE_EPSILON || Math.abs(top - second) < TIE_EPSILON;
}

function rankStyle(first: boolean): CSSProperties {
  return {
    display: "flex",
    gap: 12,
    alignItems: "flex-start",
    width: "100%",
    background: first ? C.yellow : C.cream,
    color: C.ink,
    border: `3px solid ${C.ink}`,
    borderRadius: 4,
    padding: "13px 14px",
    cursor: "pointer",
    textAlign: "left",
    boxShadow: "4px 4px 0 rgba(0,0,0,.5)",
    textDecoration: "none",
  };
}

function TraitBars({ traits }: { traits: Result["top_traits"] }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {traits.map((t) => {
        const pct = Math.round(t.score * 100);
        return (
          <div key={t.trait} style={{ display: "flex", flexDirection: "column", gap: 5 }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "baseline",
                gap: 10,
              }}
            >
              <span style={{ font: `700 14px/1.2 ${FONT.body}` }}>{traitLabel(t.trait)}</span>
              <span style={{ font: `900 14px/1 ${FONT.display}`, color: C.red }}>{pct}%</span>
            </div>
            <div style={barTrack}>
              <div style={barFill(pct)} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function NoClearDirection({
  result,
  blurbs,
}: {
  result: Result;
  blurbs: Record<string, string>;
}) {
  const three = result.top_matches.slice(0, 3);

  return (
    <div className="tq-in" style={{ maxWidth: 820, margin: "0 auto", padding: "26px 16px 0" }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 22 }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/tq-logo.png"
          alt="Taqneeq"
          style={{
            width: 84,
            height: 84,
            display: "block",
            borderRadius: "50%",
            border: `3px solid ${C.yellow}`,
            boxShadow: "0 0 0 7px rgba(254,196,0,.12), 0 0 0 10px rgba(254,196,0,.26)",
          }}
        />
        <div style={{ width: "100%", maxWidth: 660 }}>
          <div className="tq-rule" style={{ height: 8 }} />
          <h1 className="tq-display tq-display-md" style={{ fontSize: "clamp(34px,8.4vw,62px)" }}>
            No clear
            <br />
            direction yet
          </h1>
        </div>
        <p
          style={{
            maxWidth: "52ch",
            margin: 0,
            fontSize: 16,
            lineHeight: 1.6,
            color: C.text,
            textWrap: "pretty",
          }}
        >
          Your answers came out close to even across all fifteen departments. That isn&apos;t a bad
          outcome — it usually means you&apos;re genuinely flexible, or that you haven&apos;t done
          enough of this work yet to have strong preferences. Either way, we&apos;d rather say so
          than invent a winner.
        </p>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit,minmax(260px,1fr))",
          gap: 16,
          marginTop: 32,
          alignItems: "start",
        }}
      >
        <div style={purplePanel}>
          <h2 style={{ ...monoLabel(C.yellow), marginBottom: 6 }}>THREE TO GO AND LOOK AT</h2>
          <p style={{ margin: "0 0 14px", fontSize: 12, lineHeight: 1.5, color: C.lilac }}>
            Unranked — pick whichever sounds like a semester you&apos;d enjoy.
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {three.map((d) => (
              <Link
                key={d.id}
                href={`/departments/${d.id}`}
                className="tq-rank-lift"
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: 6,
                  alignItems: "flex-start",
                  width: "100%",
                  background: C.cream,
                  color: C.ink,
                  border: `3px solid ${C.ink}`,
                  borderRadius: 4,
                  padding: "13px 14px",
                  textAlign: "left",
                  boxShadow: "4px 4px 0 rgba(0,0,0,.5)",
                  textDecoration: "none",
                }}
              >
                <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ ...diamond, marginTop: 0, width: 9, height: 9 }} />
                  <span
                    style={{
                      font: `700 9px/1 ${FONT.mono}`,
                      letterSpacing: ".16em",
                      color: C.inkSoft,
                    }}
                  >
                    WORTH A LOOK
                  </span>
                </span>
                <span style={{ font: `900 16px/1.15 ${FONT.body}` }}>{d.name}</span>
                <span style={{ fontSize: 12, lineHeight: 1.35, color: C.inkMid }}>
                  {blurbs[d.id] ?? ""}
                </span>
              </Link>
            ))}
          </div>
        </div>

        <div style={creamPanel}>
          <h2 style={{ ...monoLabel(C.inkSoft), marginBottom: 4 }}>YOUR TRAIT PROFILE</h2>
          <p style={{ margin: "0 0 14px", fontSize: 12, lineHeight: 1.45, color: C.inkSoft }}>
            Your strongest measured traits, tie or not.
          </p>
          <TraitBars traits={result.top_traits} />
          <p style={{ margin: "16px 0 0", fontSize: 13, lineHeight: 1.5, color: C.inkMid }}>
            These are real measurements. Lead with them when you talk to a department head.
          </p>
        </div>
      </div>

      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 14,
          justifyContent: "center",
          marginTop: 26,
        }}
      >
        <Link
          href="/departments"
          className="tq-btn-primary"
          style={{ fontSize: 15, padding: "15px 22px", boxShadow: `5px 5px 0 ${C.red}`, textDecoration: "none" }}
        >
          Browse all 15 departments
        </Link>
        <Link
          href="/quiz"
          className="tq-btn-ghost"
          style={{
            fontFamily: FONT.display,
            fontWeight: 900,
            fontSize: 15,
            letterSpacing: ".04em",
            textTransform: "uppercase",
            padding: "15px 22px",
            borderWidth: 3,
            textDecoration: "none",
          }}
        >
          Retake the quiz
        </Link>
      </div>
    </div>
  );
}

export function ResultSummary({
  result,
  departments,
}: {
  result: Result;
  departments: Department[];
}) {
  const blurbs: Record<string, string> = {};
  departments.forEach((d) => {
    blurbs[d.id] = d.description;
  });

  if (hasNoClearSignal(result)) {
    return <NoClearDirection result={result} blurbs={blurbs} />;
  }

  const { recommended_department, runner_up, top_matches, top_traits, explanation } = result;
  const strongest = top_traits.map((t) => traitLabel(t.trait).toLowerCase());
  const why =
    strongest.length >= 3
      ? `You scored highest on ${strongest[0]}, ${strongest[1]} and ${strongest[2]} — which is close to what ${recommended_department.name} runs on.`
      : `Your strongest traits line up with what ${recommended_department.name} runs on.`;

  return (
    <div className="tq-in" style={{ maxWidth: 960, margin: "0 auto", padding: "26px 16px 0" }}>
      <div style={{ textAlign: "center" }}>
        <span
          style={{
            display: "inline-block",
            font: `700 11px/1 ${FONT.mono}`,
            letterSpacing: ".24em",
            color: C.ink,
            background: C.yellow,
            border: `2px solid ${C.ink}`,
            padding: "7px 12px",
            transform: "rotate(-1.4deg)",
          }}
        >
          {matchStrengthLabel(recommended_department.probability).toUpperCase()}
        </span>
        <div style={{ maxWidth: 760, margin: "20px auto 0" }}>
          <div className="tq-rule" style={{ height: 8 }} />
          <h1 className="tq-display tq-display-md" style={{ fontSize: "clamp(38px,10vw,74px)" }}>
            {recommended_department.name}
          </h1>
        </div>
        <p
          style={{
            maxWidth: "52ch",
            margin: "20px auto 0",
            fontSize: 16,
            lineHeight: 1.55,
            color: C.text,
          }}
        >
          {blurbs[recommended_department.id] ?? ""}
        </p>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit,minmax(280px,1fr))",
          gap: 16,
          marginTop: 34,
          alignItems: "start",
        }}
      >
        <div style={purplePanel}>
          <h2 style={{ ...monoLabel(C.yellow), marginBottom: 14 }}>YOUR TOP THREE</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {top_matches.slice(0, 3).map((d, i) => (
              <Link
                key={d.id}
                href={`/departments/${d.id}`}
                className="tq-rank-lift"
                style={rankStyle(i === 0)}
              >
                <span
                  style={{
                    flex: "none",
                    font: `900 26px/1 ${FONT.display}`,
                    letterSpacing: "-.05em",
                    opacity: 0.9,
                  }}
                >
                  #{i + 1}
                </span>
                <span style={{ display: "flex", flexDirection: "column", gap: 3, textAlign: "left" }}>
                  <span style={{ font: `900 16px/1.15 ${FONT.body}` }}>{d.name}</span>
                  <span style={{ font: `400 12px/1.35 ${FONT.body}`, opacity: 0.75 }}>
                    {blurbs[d.id] ?? ""}
                  </span>
                </span>
              </Link>
            ))}
          </div>
          <p style={{ margin: "14px 0 0", fontSize: 12, lineHeight: 1.5, color: C.lilac }}>
            All three are worth talking to. The order is a nudge, not a verdict — the right fit is
            somewhere in this list.
          </p>
        </div>

        <div style={creamPanel}>
          <h2 style={{ ...monoLabel(C.inkSoft), marginBottom: 6 }}>WHY THIS FITS YOU</h2>
          <p style={{ margin: "0 0 20px", font: `700 17px/1.4 ${FONT.body}`, textWrap: "pretty" }}>
            {why}
          </p>
          <h2 style={{ ...monoLabel(C.inkSoft), marginBottom: 12 }}>YOUR STRONGEST TRAITS</h2>
          <TraitBars traits={top_traits} />
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={darkPanel}>
            <h2 style={{ ...monoLabel(C.yellow), marginBottom: 12 }}>WHAT YOU&apos;LL DO</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {explanation.what_youll_do.map((text) => (
                <div key={text} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                  <span style={diamond} />
                  <span style={{ fontSize: 14, lineHeight: 1.45, color: C.text }}>{text}</span>
                </div>
              ))}
            </div>
          </div>
          <div style={darkPanel}>
            <h2 style={{ ...monoLabel(C.yellow), marginBottom: 12 }}>SKILLS YOU&apos;LL GAIN</h2>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {explanation.skills_gained.map((skill) => (
                <span
                  key={skill}
                  style={{
                    font: `700 12px/1 ${FONT.body}`,
                    letterSpacing: ".02em",
                    color: C.ink,
                    background: C.yellow,
                    border: `2px solid ${C.ink}`,
                    borderRadius: 99,
                    padding: "8px 12px",
                  }}
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 16,
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: 26,
          background: C.red,
          border: `3px solid ${C.ink}`,
          borderRadius: 5,
          padding: "18px 20px",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <span
            style={{
              font: `700 10px/1 ${FONT.mono}`,
              letterSpacing: ".22em",
              color: "rgba(255,255,255,.8)",
            }}
          >
            ALSO WORTH A LOOK
          </span>
          <span
            style={{
              font: `900 22px/1.1 ${FONT.display}`,
              letterSpacing: "-.02em",
              color: "#fff",
            }}
          >
            {runner_up.name}
          </span>
        </div>
        <Link
          href={`/departments/${runner_up.id}`}
          className="tq-rank-lift"
          style={{
            font: `900 13px/1 ${FONT.display}`,
            letterSpacing: ".06em",
            textTransform: "uppercase",
            background: C.yellow,
            color: C.ink,
            border: `3px solid ${C.ink}`,
            borderRadius: 3,
            padding: "13px 18px",
            boxShadow: "4px 4px 0 rgba(0,0,0,.5)",
            textDecoration: "none",
          }}
        >
          Read about it →
        </Link>
      </div>

      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 14,
          justifyContent: "center",
          marginTop: 24,
        }}
      >
        <Link href="/departments" className="tq-btn-ghost" style={{ textDecoration: "none" }}>
          BROWSE ALL 15 DEPARTMENTS
        </Link>
        <Link href="/quiz" className="tq-btn-ghost" style={{ textDecoration: "none" }}>
          RETAKE THE QUIZ
        </Link>
      </div>
    </div>
  );
}
