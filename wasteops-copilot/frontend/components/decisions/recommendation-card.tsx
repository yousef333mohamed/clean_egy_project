import type { DecisionOption } from "@/lib/schemas/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { OptionScoreBreakdown } from "./option-score-breakdown";
export function RecommendationCard({ option }: { option: DecisionOption }) {
  return (
    <Card className="border-primary/40">
      <CardHeader>
        <div className="flex flex-wrap gap-2">
          <Badge>{option.priority}</Badge>
          <Badge>{option.action_category}</Badge>
        </div>
        <CardTitle>{option.title}</CardTitle>
        <p className="text-muted-foreground text-sm">{option.action}</p>
      </CardHeader>
      <CardContent className="grid gap-6 md:grid-cols-2">
        <OptionScoreBreakdown option={option} />
        <div className="space-y-3">
          <div>
            <p className="text-sm font-medium">Evidence types</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {option.supporting_evidence_ids.map((id) => (
                <Badge key={id}>
                  [{id}] {id.startsWith("M") ? "Prediction" : id.startsWith("D") ? "Historical fact" : id.startsWith("R") ? "Configured rule" : "Document guidance"}
                </Badge>
              ))}
            </div>
            <p className="text-muted-foreground mt-2 text-xs">Model evidence is not official policy, and prediction probability is not the decision confidence score.</p>
          </div>
          <List title="Expected impact" values={option.expected_impact} />
          <List title="Assumptions" values={option.assumptions} />
          <List
            title="Risks and trade-offs"
            values={[...option.possible_risks, ...option.trade_offs]}
          />
        </div>
      </CardContent>
    </Card>
  );
}
function List({ title, values }: { title: string; values: string[] }) {
  return (
    <div>
      <p className="text-sm font-medium">{title}</p>
      {values.length ? (
        <ul className="text-muted-foreground mt-1 list-inside list-disc text-sm">
          {values.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="text-muted-foreground text-sm">None supplied</p>
      )}
    </div>
  );
}
