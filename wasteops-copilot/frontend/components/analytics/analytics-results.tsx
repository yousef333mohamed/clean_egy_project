import type { AnalyticsResponse } from "@/lib/schemas/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AnswerWarning } from "@/components/assistant/answer-warning";
import { DatabaseEvidenceCard } from "./database-evidence-card";
import { FeedbackForm } from "@/components/feedback/feedback-form";
export function AnalyticsResults({ result }: { result: AnalyticsResponse }) {
  return (
    <div className="space-y-5">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap gap-2">
            <Badge>{result.route}</Badge>
            {result.domain && <Badge>{result.domain}</Badge>}
            {result.tool_name && <Badge>{result.tool_name}</Badge>}
          </div>
          <CardTitle>Structured answer</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="whitespace-pre-wrap">{result.answer}</p>
          {result.insufficient_data && (
            <AnswerWarning>
              No matching data was available for the requested scope.
            </AnswerWarning>
          )}
          {result.warnings.map((warning) => (
            <AnswerWarning key={warning}>{warning}</AnswerWarning>
          ))}
          <code className="text-muted-foreground block text-xs">
            Request {result.request_id}
          </code>
          <FeedbackForm requestId={result.request_id} />
        </CardContent>
      </Card>
      {result.database_evidence.map((evidence) => (
        <DatabaseEvidenceCard key={evidence.evidence_id} evidence={evidence} />
      ))}
    </div>
  );
}
