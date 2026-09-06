import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center gap-8 text-center">
      <p className="text-sm uppercase tracking-[0.3em] text-taqneeq-violet">Taqneeq</p>
      <h1 className="text-4xl font-bold text-white sm:text-6xl">Find your department</h1>
      <p className="max-w-xl text-white/70">
        Answer a short set of questions about how you like to work, and we&apos;ll match you to the Taqneeq
        department where you&apos;ll thrive - from Technicals to Marketing to Hospitality and beyond.
      </p>
      <Link
        href="/quiz"
        className="rounded-full bg-taqneeq-violet px-8 py-3 text-lg font-semibold text-white shadow-lg shadow-taqneeq-violet/30 transition-transform hover:scale-105"
      >
        Start the quiz
      </Link>
      <Link href="/departments" className="text-sm text-white/60 underline hover:text-white">
        Or browse all departments first
      </Link>
    </div>
  );
}
