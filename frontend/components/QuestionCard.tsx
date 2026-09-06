import type { CSSProperties } from "react";
import { C, FONT, badge, dashedRule, pad } from "@/lib/theme";
import type { Question } from "@/types/api";

function optionStyle(selected: boolean, dimmed: boolean): CSSProperties {
  return {
    display: "flex",
    alignItems: "center",
    gap: 12,
    width: "100%",
    font: `700 15px/1.25 ${FONT.body}`,
    background: selected ? C.yellow : C.cream,
    color: C.ink,
    border: `3px solid ${C.ink}`,
    borderRadius: 4,
    padding: "12px 14px",
    cursor: dimmed ? "default" : "pointer",
    boxShadow: selected ? `4px 4px 0 ${C.red}` : `3px 3px 0 ${C.ink}`,
    opacity: dimmed && !selected ? 0.45 : 1,
    transition: "transform .12s ease, box-shadow .12s ease, background .12s ease",
  };
}

export function QuestionCard({
  question,
  number,
  selected,
  locked,
  onSelect,
}: {
  question: Question;
  number: number;
  selected: number | null;
  locked: boolean;
  onSelect: (value: number) => void;
}) {
  return (
    <div
      style={{
        background: C.cream,
        color: C.ink,
        border: `3px solid ${C.ink}`,
        borderRadius: 5,
        boxShadow: "8px 8px 0 rgba(0,0,0,.55)",
        padding: "24px 20px 22px",
        marginTop: 22,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
        <span style={badge(40, C.cream)}>{pad(number)}</span>
        <span style={dashedRule} />
        <span
          style={{
            flex: "none",
            font: `700 10px/1 ${FONT.mono}`,
            letterSpacing: ".16em",
            color: C.inkSoft,
          }}
        >
          HOW LIKE YOU?
        </span>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/tq-logo.png"
          alt=""
          style={{ flex: "none", width: 26, height: 26, display: "block", borderRadius: "50%" }}
        />
      </div>

      <p
        style={{
          margin: "0 0 20px",
          font: `700 clamp(21px,5.4vw,28px)/1.22 ${FONT.body}`,
          letterSpacing: "-.015em",
          textWrap: "pretty",
        }}
      >
        {question.text}
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: 9 }}>
        {question.options.map((option) => {
          const isSelected = selected === option.value;
          return (
            <button
              key={option.value}
              type="button"
              className="tq-lift"
              disabled={locked}
              onClick={() => onSelect(option.value)}
              style={optionStyle(isSelected, locked)}
            >
              <span
                style={{
                  flex: "none",
                  width: 26,
                  height: 26,
                  borderRadius: "50%",
                  border: "2px solid currentColor",
                  display: "grid",
                  placeItems: "center",
                  font: `900 12px/1 ${FONT.display}`,
                }}
              >
                {option.value}
              </span>
              <span style={{ textAlign: "left" }}>{option.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
