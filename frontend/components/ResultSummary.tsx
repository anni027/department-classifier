import Link from "next/link";
import type { Result } from "@/types/api";

function traitLabel(trait: string): string {
  return trait
    .split("_")
    .map((word) => word[0].toUpperCase() + word.slice(1))
    .join(" ");
}

export function ResultSummary({ result }: { result: Result }) {
  const { recommended_department, runner_up, top_matches, top_traits, explanation } = result;
  const matchPct = Math.round(recommended_department.probability * 100);

  return (
    <div className="flex flex-col gap-8">
      <div className="rounded-3xl border border-taqneeq-violet/40 bg-gradient-to-br from-taqneeq-violet/20 to-transparent p-8 text-center">
        <p className="text-sm uppercase tracking-widest text-white/60">Your best match</p>
        <h1 className="mt-2 text-4xl font-bold text-white sm:text-5xl">{recommended_department.name}</h1>
        <p className="mt-2 text-xl font-semibold text-taqneeq-violet">{matchPct}% Match</p>
      </div>

      <section className="rounded-2xl border border-white/10 bg-white/5 p-6">
        <h2 className="mb-3 text-lg font-semibold text-white">Top matches</h2>
        <div className="flex flex-col gap-2">
          {top_matches.map((match, i) => (
            <div
              key={match.id}
              className={`flex items-center justify-between rounded-xl border px-4 py-3 ${
                i === 0 ? "border-taqneeq-violet/60 bg-taqneeq-violet/10" : "border-white/10"
              }`}
            >
              <span className="flex items-center gap-3">
                <span className="text-sm font-semibold text-white/50">#{i + 1}</span>
                <span className="font-medium text-white">{match.name}</span>
              </span>
              <span className="text-sm text-white/70">{Math.round(match.probability * 100)}%</span>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-white/10 bg-white/5 p-6">
        <h2 className="mb-3 text-lg font-semibold text-white">Why this fits you</h2>
        <p className="text-sm text-white/70">
          Your responses showed strong{" "}
          {top_traits.map((t, i) => (
            <span key={t.trait}>
              {i > 0 && (i === top_traits.length - 1 ? " and " : ", ")}
              <span className="font-medium text-white">{traitLabel(t.trait).toLowerCase()}</span>
            </span>
          ))}
          . These traits line up closely with how {recommended_department.name} works.
        </p>
      </section>

      <section className="rounded-2xl border border-white/10 bg-white/5 p-6">
        <h2 className="mb-3 text-lg font-semibold text-white">Your strongest traits</h2>
        <div className="flex flex-wrap gap-2">
          {top_traits.map((t) => (
            <span key={t.trait} className="rounded-full bg-taqneeq-violet/20 px-3 py-1 text-sm text-white">
              {traitLabel(t.trait)} · {Math.round(t.score * 100)}%
            </span>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-white/10 bg-white/5 p-6">
        <h2 className="mb-3 text-lg font-semibold text-white">What you&apos;ll do</h2>
        <ul className="list-inside list-disc space-y-1 text-sm text-white/70">
          {explanation.what_youll_do.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="rounded-2xl border border-white/10 bg-white/5 p-6">
        <h2 className="mb-3 text-lg font-semibold text-white">Skills you&apos;ll gain</h2>
        <div className="flex flex-wrap gap-2">
          {explanation.skills_gained.map((skill) => (
            <span key={skill} className="rounded-full border border-white/20 px-3 py-1 text-sm text-white/80">
              {skill}
            </span>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-white/10 bg-white/5 p-6">
        <h2 className="mb-3 text-lg font-semibold text-white">Also worth a look</h2>
        <p className="text-sm text-white/70">
          You also scored well for{" "}
          <Link href={`/departments/${runner_up.id}`} className="font-medium text-taqneeq-violet underline">
            {runner_up.name}
          </Link>{" "}
          ({Math.round(runner_up.probability * 100)}% match).
        </p>
      </section>

      <Link
        href="/departments"
        className="inline-block w-fit rounded-full border border-white/20 px-5 py-2 text-sm text-white/80 hover:bg-white/10"
      >
        Browse all departments
      </Link>
    </div>
  );
}
