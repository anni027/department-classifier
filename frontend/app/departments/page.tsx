import Link from "next/link";
import { DepartmentCard } from "@/components/DepartmentCard";
import { ApiError, listDepartments } from "@/lib/api";
import { C } from "@/lib/theme";

export const dynamic = "force-dynamic";

export default async function DepartmentsPage() {
  let departments;
  try {
    departments = await listDepartments();
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 0;
    const detail =
      status === 0
        ? "Could not reach the server. It may be waking up — give it a moment and try again."
        : `Request failed (${status}).`;
    return (
      <div style={{ maxWidth: 1080, margin: "0 auto", padding: "26px 16px 0" }}>
        <Link href="/" className="tq-back" style={{ display: "inline-block", textDecoration: "none" }}>
          ← BACK
        </Link>
        <div style={{ display: "inline-block", marginTop: 16 }}>
          <div className="tq-rule" style={{ height: 8 }} />
          <h1 className="tq-display tq-display-md" style={{ fontSize: "clamp(34px,8vw,62px)" }}>
            Departments
          </h1>
        </div>
        <p style={{ maxWidth: "52ch", margin: "18px 0 0", fontSize: 16, lineHeight: 1.55, color: C.text }}>{detail}</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1080, margin: "0 auto", padding: "26px 16px 0" }}>
      <Link href="/" className="tq-back" style={{ display: "inline-block", textDecoration: "none" }}>
        ← BACK
      </Link>

      <div style={{ display: "inline-block", marginTop: 16 }}>
        <div className="tq-rule" style={{ height: 8 }} />
        <h1 className="tq-display tq-display-md" style={{ fontSize: "clamp(34px,8vw,62px)" }}>
          All {departments.length} departments
        </h1>
      </div>

      <p style={{ maxWidth: "52ch", margin: "18px 0 0", fontSize: 16, lineHeight: 1.55, color: C.text }}>
        Every one of them needs people for the whole run-up, not just the three days of the festival.
      </p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill,minmax(240px,1fr))",
          gap: 14,
          marginTop: 28,
        }}
      >
        {departments.map((department, index) => (
          <DepartmentCard key={department.id} department={department} index={index} />
        ))}
      </div>
    </div>
  );
}