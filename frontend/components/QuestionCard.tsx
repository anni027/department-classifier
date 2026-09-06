import type { Question } from "@/types/api";

export function QuestionCard({
  question,
  selected,
  onSelect,
}: {
  question: Question;
  selected: number | null;
  onSelect: (value: number) => void;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-6 shadow-xl backdrop-blur">
      <p className="mb-6 text-lg font-medium leading-relaxed text-white sm:text-xl">{question.text}</p>
      <div className="flex flex-col gap-2">
        {question.options.map((option) => {
          const isSelected = selected === option.value;
          return (
            <button
              key={option.value}
              type="button"
              onClick={() => onSelect(option.value)}
              className={`rounded-xl border px-4 py-3 text-left text-sm transition-colors sm:text-base ${
                isSelected
                  ? "border-taqneeq-violet bg-taqneeq-violet/20 text-white"
                  : "border-white/10 bg-transparent text-white/80 hover:border-white/30 hover:bg-white/5"
              }`}
            >
              <span className="mr-2 font-semibold">{option.value}</span>
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
