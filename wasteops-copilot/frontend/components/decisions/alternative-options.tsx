import type { DecisionOption } from "@/lib/schemas/api";
import { OptionScoreBreakdown } from "./option-score-breakdown";
export function AlternativeOptions({ options }: { options: DecisionOption[] }) {
  if (!options.length) return null;
  return (
    <section>
      <h2 className="mb-3 text-lg font-semibold">Alternative options</h2>
      <div className="space-y-3">
        {options.map((option) => (
          <details
            key={option.option_id}
            className="bg-card rounded-xl border p-4"
          >
            <summary className="cursor-pointer font-medium">
              {option.title} · {(option.score * 100).toFixed(1)}
            </summary>
            <div className="mt-4">
              <p className="text-muted-foreground mb-4 text-sm">
                {option.action}
              </p>
              <OptionScoreBreakdown option={option} />
            </div>
          </details>
        ))}
      </div>
    </section>
  );
}
