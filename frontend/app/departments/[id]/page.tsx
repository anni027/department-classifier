import Link from "next/link";
import { notFound } from "next/navigation";
import { ApiError, getDepartment, getSimilarDepartments } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DepartmentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  let department;
  let similar;
  try {
    [department, similar] = await Promise.all([getDepartment(id), getSimilarDepartments(id)]);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  const topTraits = Object.entries(department.weights)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);

  return (
    <div className="flex flex-col gap-8">
      <Link href="/departments" className="text-sm text-white/60 hover:text-white">
        ← Back to all departments
      </Link>

      <div>
        <h1 className="text-3xl font-bold text-white sm:text-4xl">{department.name}</h1>
        <p className="mt-3 text-white/70">{department.description}</p>
      </div>

      <section className="rounded-2xl border border-white/10 bg-white/5 p-6">
        <h2 className="mb-3 text-lg font-semibold text-white">What matters most here</h2>
        <div className="flex flex-wrap gap-2">
          {topTraits.map(([trait, weight]) => (
            <span key={trait} className="rounded-full bg-taqneeq-violet/20 px-3 py-1 text-sm text-white">
              {trait.replaceAll("_", " ")} · {Math.round(weight * 100)}%
            </span>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-white/10 bg-white/5 p-6">
        <h2 className="mb-3 text-lg font-semibold text-white">Similar departments</h2>
        <div className="flex flex-col gap-2">
          {similar.map((d) => (
            <Link
              key={d.id}
              href={`/departments/${d.id}`}
              className="flex items-center justify-between rounded-xl border border-white/10 px-4 py-2 text-sm text-white/80 hover:bg-white/10"
            >
              <span>{d.name}</span>
              <span className="text-white/50">{Math.round(d.similarity * 100)}% similar</span>
            </Link>
          ))}
        </div>
      </section>

      <Link
        href="/quiz"
        className="w-fit rounded-full bg-taqneeq-violet px-6 py-2 font-semibold text-white hover:scale-105 transition-transform"
      >
        Take the quiz
      </Link>
    </div>
  );
}
