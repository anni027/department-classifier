import Link from "next/link";
import { C, FONT } from "@/lib/theme";

const SWATCHES = [C.yellow, C.red, "#7A2CC1", C.cream];

export default function LandingPage() {
  return (
    <div style={{ maxWidth: 720, margin: "0 auto", padding: "56px 20px 0", textAlign: "center" }}>
      <div
        style={{
          display: "inline-flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 10,
          marginBottom: 26,
        }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/tq-logo.png"
          alt="Taqneeq"
          style={{
            width: 92,
            height: 92,
            display: "block",
            borderRadius: "50%",
            border: `3px solid ${C.yellow}`,
            boxShadow: "0 0 0 6px rgba(254,196,0,.14)",
          }}
        />
        <span
          style={{
            font: `700 11px/1 ${FONT.mono}`,
            letterSpacing: ".34em",
            color: C.lilac,
          }}
        >
          TAQNEEQ · RECRUITMENT
        </span>
      </div>

      <div style={{ display: "inline-block", textAlign: "left" }}>
        <div className="tq-rule" />
        <h1 className="tq-display" style={{ fontSize: "clamp(46px,13vw,96px)" }}>
          Find your
          <br />
          department
        </h1>
      </div>

      <p
        style={{
          maxWidth: "44ch",
          margin: "26px auto 0",
          fontSize: 17,
          lineHeight: 1.55,
          color: C.text,
          textWrap: "pretty",
        }}
      >
        Fifteen departments run this festival. Answer fifteen quick statements about how you actually
        like to work, and we&apos;ll tell you where you&apos;d fit — plus the two runners-up worth a
        look.
      </p>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 18,
          marginTop: 34,
        }}
      >
        <Link
          href="/quiz"
          className="tq-btn-primary"
          style={{
            fontSize: 20,
            lineHeight: 1,
            padding: "18px 34px",
            display: "inline-block",
            textDecoration: "none",
          }}
        >
          Start the quiz →
        </Link>
        <Link href="/departments" className="tq-link-quiet" style={{ display: "inline-block" }}>
          Or browse all departments first
        </Link>

        <div style={{ display: "flex", gap: 5, marginTop: 8 }}>
          {SWATCHES.map((colour) => (
            <span key={colour} style={{ width: 34, height: 8, background: colour }} />
          ))}
        </div>

        <span
          style={{
            font: `700 10px/1.6 ${FONT.mono}`,
            letterSpacing: ".2em",
            color: C.muted,
            textAlign: "center",
          }}
        >
          3 MINUTES · NO SIGN-UP · 15 QUESTIONS MAX
        </span>
      </div>
    </div>
  );
}
