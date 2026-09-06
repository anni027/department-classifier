import { C, FONT } from "@/lib/theme";

/**
 * The design's tick strip: one tick per question slot, filled for answered,
 * hatched for the current one, outlined for the rest.
 *
 * `max` is the API's `total_max_questions` — a ceiling, not a promise. A
 * session can end a question or two early, which is what the note says.
 */
export function ProgressBar({ current, max }: { current: number; max: number }) {
  const index = current - 1;

  return (
    <>
      <div style={{ display: "flex", gap: 3, marginBottom: 4 }}>
        {Array.from({ length: max }, (_, i) => (
          <span
            key={i}
            style={{
              flex: 1,
              height: 10,
              border: `1px solid ${i <= index ? C.yellow : "rgba(201,166,245,.35)"}`,
              background:
                i < index
                  ? C.yellow
                  : i === index
                    ? `repeating-linear-gradient(45deg,${C.yellow} 0 3px,${C.purpleDeep} 3px 6px)`
                    : "transparent",
            }}
          />
        ))}
      </div>
      <div
        style={{
          font: `700 10px/1.8 ${FONT.mono}`,
          letterSpacing: ".18em",
          color: C.muted,
        }}
      >
        {current < max - 4
          ? `SOME SESSIONS END EARLY — ${max} IS THE MAXIMUM`
          : "ALMOST THERE · A FEW LEFT AT MOST"}
      </div>
    </>
  );
}
