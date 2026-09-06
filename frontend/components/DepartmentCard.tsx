import Link from "next/link";
import { C, FONT, badge, pad } from "@/lib/theme";
import type { Department } from "@/types/api";

/**
 * The design numbers each department card rather than using an icon —
 * the emoji set the old cards used has no place in this treatment.
 */
export function DepartmentCard({ department, index }: { department: Department; index: number }) {
  return (
    <Link
      href={`/departments/${department.id}`}
      className="tq-card-lift"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 12,
        alignItems: "flex-start",
        background: C.cream,
        color: C.ink,
        border: `3px solid ${C.ink}`,
        borderRadius: 5,
        padding: 16,
        textAlign: "left",
        boxShadow: "5px 5px 0 rgba(0,0,0,.55)",
        textDecoration: "none",
      }}
    >
      <span style={{ display: "flex", alignItems: "center", gap: 10, width: "100%" }}>
        <span style={{ ...badge(38, C.cream), boxShadow: `0 0 0 2px ${C.cream}, 0 0 0 4px ${C.purpleDeep}` }}>
          {pad(index + 1)}
        </span>
        <span
          style={{
            flex: 1,
            height: 3,
            background: `repeating-linear-gradient(90deg,${C.ink} 0 6px,transparent 6px 11px)`,
          }}
        />
      </span>
      <span style={{ font: `900 17px/1.12 ${FONT.body}`, letterSpacing: "-.01em" }}>
        {department.name}
      </span>
      <span style={{ fontSize: 13, lineHeight: 1.45, color: C.inkMid }}>
        {department.description}
      </span>
    </Link>
  );
}
