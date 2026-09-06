import Link from "next/link";
import { notFound } from "next/navigation";
import { ApiError, getDepartment, getSimilarDepartments, listDepartments } from "@/lib/api";
import {
  C,
  FONT,
  barTrack,
  creamPanel,
  darkPanel,
  diamond,
  monoLabel,
  pad,
  purplePanel,
  traitLabel,
} from "@/lib/theme";

export const dynamic = "force-dynamic";

export default async function DepartmentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  let department;
  let similar;
  let all;
  try {
    [department, similar, all] = await Promise.all([
      getDepartment(id),
      getSimilarDepartments(id),
      listDepartments(),
    ]);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  const position = all.findIndex((d) => d.id === department.id);
  const topWeights = Object.entries(department.weights)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);

  return (
    <div style={{ maxWidth: 820, margin: "0 auto", padding: "26px 16px 0" }}>
      <Link
        href="/departments"
        className="tq-back"
        style={{ display: "inline-block", textDecoration: "none" }}
      >
        ← ALL DEPARTMENTS
      </Link>

      <div style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 18 }}>
        <span
          style={{
            flex: "none",
            width: 52,
            height: 52,
            borderRadius: "50%",
            background: C.purpleDeep,
            color: C.yellow,
            display: "grid",
            placeItems: "center",
            font: `900 18px/1 ${FONT.display}`,
            border: `3px solid ${C.yellow}`,
          }}
        >
          {pad(position >= 0 ? position + 1 : 1)}
        </span>
        <div style={{ flex: 1 }}>
          <div className="tq-rule" style={{ height: 7 }} />
          <h1 className="tq-display tq-display-sm" style={{ fontSize: "clamp(28px,7vw,52px)" }}>
            {department.name}
          </h1>
        </div>
      </div>

      <p
        style={{
          maxWidth: "56ch",
          margin: "20px 0 0",
          fontSize: 16,
          lineHeight: 1.6,
          color: C.text,
          textWrap: "pretty",
        }}
      >
        {department.description}
      </p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit,minmax(260px,1fr))",
          gap: 16,
          marginTop: 28,
          alignItems: "start",
        }}
      >
        <div style={creamPanel}>
          <h2 style={{ ...monoLabel(C.inkSoft), marginBottom: 4 }}>WHAT MATTERS MOST HERE</h2>
          <p style={{ margin: "0 0 14px", fontSize: 12, lineHeight: 1.45, color: C.inkSoft }}>
            How this department is weighted in the matcher.
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: 11 }}>
            {topWeights.map(([trait, weight]) => {
              const pct = Math.round(weight * 100);
              return (
                <div key={trait} style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "baseline",
                      gap: 10,
                    }}
                  >
                    <span style={{ font: `700 13px/1.2 ${FONT.body}` }}>{traitLabel(trait)}</span>
                    <span style={{ font: `900 13px/1 ${FONT.display}`, color: C.bar }}>{pct}%</span>
                  </div>
                  <div style={{ ...barTrack, height: 10 }}>
                    <div style={{ height: "100%", width: `${pct}%`, background: C.bar }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={darkPanel}>
            <h2 style={{ ...monoLabel(C.yellow), marginBottom: 12 }}>WHAT YOU&apos;LL DO</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {department.responsibilities.map((text) => (
                <div key={text} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                  <span style={diamond} />
                  <span style={{ fontSize: 14, lineHeight: 1.45, color: C.text }}>{text}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={purplePanel}>
            <h2 style={{ ...monoLabel(C.yellow), marginBottom: 12 }}>SIMILAR DEPARTMENTS</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {similar.slice(0, 3).map((s) => (
                <Link key={s.id} href={`/departments/${s.id}`} className="tq-similar">
                  <span>{s.name}</span>
                  <span style={{ opacity: 0.6 }}>→</span>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "center", marginTop: 28 }}>
        <Link
          href="/quiz"
          className="tq-btn-primary"
          style={{
            fontSize: 16,
            padding: "15px 24px",
            boxShadow: `5px 5px 0 ${C.red}`,
            textDecoration: "none",
          }}
        >
          Take the quiz →
        </Link>
      </div>
    </div>
  );
}
