import type { DecisionOption } from "@/lib/schemas/api";
const labels = {
  service_impact: "Service impact",
  urgency: "Urgency",
  risk_control: "Risk control",
  feasibility: "Feasibility",
  policy_alignment: "Policy alignment",
};
export function OptionScoreBreakdown({ option }: { option: DecisionOption }) {
  return (
    <div className="space-y-3">
      <p className="text-sm font-medium">
        Deterministic decision score: {(option.score * 100).toFixed(1)} / 100
      </p>
      {Object.entries(option.score_breakdown).map(([key, value]) => (
        <div key={key}>
          <div className="mb-1 flex justify-between text-xs">
            <span>{labels[key as keyof typeof labels]}</span>
            <span>{(value * 100).toFixed(1)}</span>
          </div>
          <div className="bg-muted h-2 overflow-hidden rounded-full">
            <div
              className="bg-primary h-full"
              style={{ width: `${value * 100}%` }}
            />
          </div>
        </div>
      ))}
      <p className="text-muted-foreground text-xs">
        This score is calculated by deterministic backend logic. It is not a
        probability.
      </p>
    </div>
  );
}
