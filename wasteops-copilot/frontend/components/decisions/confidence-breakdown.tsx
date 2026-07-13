import type { DecisionResponse } from "@/lib/schemas/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
const labels = {
  retrieval_coverage: "Retrieval coverage",
  source_quality: "Source quality",
  data_completeness: "Data completeness",
  source_agreement: "Source agreement",
  recency: "Recency",
};
export function ConfidenceBreakdown({
  confidence,
}: {
  confidence: DecisionResponse["confidence"];
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Evidence confidence · {confidence.level}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-2xl font-semibold">
          {(confidence.score * 100).toFixed(1)} / 100
        </p>
        {Object.entries(confidence.components).map(([key, value]) => (
          <div key={key} className="flex items-center justify-between text-sm">
            <span>{labels[key as keyof typeof labels]}</span>
            <span className="tabular-nums">{(value * 100).toFixed(1)}</span>
          </div>
        ))}
        <p className="text-muted-foreground text-sm">
          {confidence.explanation}
        </p>
        <p className="bg-muted rounded-lg p-3 text-sm font-medium">
          This confidence value measures evidence quality. It is not the
          probability that the recommendation is correct.
        </p>
      </CardContent>
    </Card>
  );
}
