import type { DecisionResponse } from "@/lib/schemas/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AnswerWarning } from "@/components/assistant/answer-warning";
import { FeedbackForm } from "@/components/feedback/feedback-form";
import { HumanApprovalBanner } from "./human-approval-banner";
import { RecommendationCard } from "./recommendation-card";
import { ConfidenceBreakdown } from "./confidence-breakdown";
import { AlternativeOptions } from "./alternative-options";
export function DecisionSummary({ result }: { result: DecisionResponse }) {
  return (
    <div className="space-y-5">
      <HumanApprovalBanner />
      <Card>
        <CardHeader>
          <CardTitle>Situation summary · {result.decision_type}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="whitespace-pre-wrap">{result.situation_summary}</p>
          {result.warnings.map((warning) => (
            <AnswerWarning key={warning}>{warning}</AnswerWarning>
          ))}
          <code className="text-muted-foreground block text-xs">
            Request {result.request_id}
          </code>
        </CardContent>
      </Card>
      {result.recommended_option ? (
        <RecommendationCard option={result.recommended_option} />
      ) : (
        <AnswerWarning>
          No recommendation was issued because the backend reported insufficient
          evidence.
        </AnswerWarning>
      )}
      <ConfidenceBreakdown confidence={result.confidence} />
      <AlternativeOptions options={result.alternative_options} />
      {result.missing_information.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Missing information</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="text-muted-foreground list-inside list-disc text-sm">
              {result.missing_information.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
      <FeedbackForm requestId={result.request_id} />
    </div>
  );
}
