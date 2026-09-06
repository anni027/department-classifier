/**
 * Design tokens and shared style fragments from the Claude Design source
 * ("Taqneeq Classifier.dc.html"). Values are the design's, verbatim.
 *
 * The design used inline styles throughout; the repeated ones live here so a
 * colour or shadow is defined once rather than pasted into every screen.
 */
import type { CSSProperties } from "react";

export const C = {
  bg: "#150528",
  panel: "#0F0421",
  purpleDeep: "#360D5D",
  yellow: "#FEC400",
  red: "#C1272D",
  cream: "#F3E7D0",
  creamDark: "#E8D8B8",
  ink: "#150528",
  text: "#E3D6F2",
  lilac: "#C9A6F5",
  muted: "#8C6BC0",
  inkSoft: "#6B4B95",
  inkMid: "#3A2158",
  bar: "#6d28d9",
  barAlt: "#8b5cf6",
} as const;

export const FONT = {
  display: "'Arial Black','Arial Bold',Impact,sans-serif",
  body: "'Helvetica Neue',Helvetica,Arial,sans-serif",
  mono: "ui-monospace,'Courier New',monospace",
} as const;

/** Two-digit index, as the design numbers its cards ("01", "02", …). */
export const pad = (n: number): string => String(n).padStart(2, "0");

/** Cream panel with a hard black keyline and offset shadow. */
export const creamPanel: CSSProperties = {
  background: C.cream,
  color: C.ink,
  border: `3px solid ${C.ink}`,
  borderRadius: 5,
  boxShadow: "7px 7px 0 rgba(0,0,0,.5)",
  padding: 20,
};

/** Deep-purple panel outlined in yellow. */
export const purplePanel: CSSProperties = {
  background: C.purpleDeep,
  border: `3px solid ${C.yellow}`,
  borderRadius: 5,
  padding: 20,
};

/** Near-black panel with a faint cream keyline. */
export const darkPanel: CSSProperties = {
  background: C.panel,
  border: "3px solid rgba(243,231,208,.28)",
  borderRadius: 5,
  padding: 20,
};

export const monoLabel = (color: string): CSSProperties => ({
  margin: 0,
  font: `700 11px/1 ${FONT.mono}`,
  letterSpacing: ".2em",
  color,
});

/** The circular numbered badge used on cards and the quiz header. */
export const badge = (size: number, ring: string): CSSProperties => ({
  flex: "none",
  width: size,
  height: size,
  borderRadius: "50%",
  background: C.purpleDeep,
  color: C.yellow,
  display: "grid",
  placeItems: "center",
  font: `900 ${Math.round(size * 0.37)}px/1 ${FONT.display}`,
  boxShadow: `0 0 0 3px ${ring}, 0 0 0 5px ${C.purpleDeep}`,
});

/** Dashed rule that fills the gap in card headers. */
export const dashedRule: CSSProperties = {
  flex: 1,
  height: 3,
  background: `repeating-linear-gradient(90deg,${C.ink} 0 8px,transparent 8px 14px)`,
};

/** Small red diamond used as a list bullet. */
export const diamond: CSSProperties = {
  flex: "none",
  width: 7,
  height: 7,
  marginTop: 7,
  background: C.red,
  transform: "rotate(45deg)",
};

/** Striped progress-bar fill for trait percentages. */
export const barFill = (pct: number): CSSProperties => ({
  height: "100%",
  width: `${Math.max(0, Math.min(100, pct))}%`,
  background: `repeating-linear-gradient(90deg,${C.bar} 0 5px,${C.barAlt} 5px 10px)`,
});

export const barTrack: CSSProperties = {
  height: 12,
  border: `2px solid ${C.ink}`,
  background: C.creamDark,
};

/** Turns `people_skills` into `People skills`. */
export function traitLabel(trait: string): string {
  const words = trait.split("_").join(" ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}
