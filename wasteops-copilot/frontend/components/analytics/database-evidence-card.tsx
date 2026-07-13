import type { OperationalEvidence } from "@/lib/schemas/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AnalyticsTable } from "./analytics-table";
import { AnalyticsChart } from "./analytics-chart";
export function DatabaseEvidenceCard({
  evidence,
}: {
  evidence: OperationalEvidence;
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center gap-2">
          <CardTitle>{evidence.description}</CardTitle>
          <Badge>{evidence.evidence_id}</Badge>
          <Badge>{evidence.tool_name}</Badge>
        </div>
        <p className="text-muted-foreground text-sm">
          Period: {evidence.data_period.start ?? "unknown"} –{" "}
          {evidence.data_period.end ?? "unknown"} · {evidence.record_count}{" "}
          records
        </p>
      </CardHeader>
      <CardContent className="space-y-5">
        <AnalyticsChart columns={evidence.columns} rows={evidence.rows} />
        <AnalyticsTable columns={evidence.columns} rows={evidence.rows} />
        {evidence.notes.length > 0 && (
          <ul className="text-muted-foreground space-y-1 text-sm">
            {evidence.notes.map((note) => (
              <li key={note}>• {note}</li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
