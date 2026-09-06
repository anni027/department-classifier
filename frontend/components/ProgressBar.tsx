export function ProgressBar({ current, max }: { current: number; max: number }) {
  const pct = Math.min(100, Math.round((current / max) * 100));
  return (
    <div className="w-full">
      <div className="mb-1 flex justify-between text-xs text-white/60">
        <span>
          Question {current} of ~{max}
        </span>
        <span>{pct}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-gradient-to-r from-taqneeq-violet to-taqneeq-purple transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
