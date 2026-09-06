import Link from "next/link";
import type { Department } from "@/types/api";

const ICONS: Record<string, string> = {
  admin: "\u{1F4CB}",
  artist_guest_management: "\u{1F3A4}",
  digital_creatives: "\u{1F3A8}",
  film_media: "\u{1F3A5}",
  hospitality: "\u{1F373}",
  informals: "\u{1F3AE}",
  in_house_creatives: "\u{1F58C}️",
  logistics: "\u{1F69A}",
  marketing: "\u{1F4C8}",
  outreach: "\u{1F91D}",
  publicity: "\u{1F4E3}",
  social_media_content: "✍️",
  technical_events: "⚙️",
  technicals: "\u{1F4BB}",
  workshops: "\u{1F393}",
};

export function DepartmentCard({ department }: { department: Department }) {
  return (
    <Link
      href={`/departments/${department.id}`}
      className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-white/5 p-5 transition-colors hover:border-taqneeq-violet/60 hover:bg-white/10"
    >
      <span className="text-3xl">{ICONS[department.id] ?? "✨"}</span>
      <h3 className="text-lg font-semibold text-white">{department.name}</h3>
      <p className="text-sm text-white/60">{department.description}</p>
    </Link>
  );
}
