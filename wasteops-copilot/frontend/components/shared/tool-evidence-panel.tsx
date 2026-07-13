"use client";
import { useQuery } from "@tanstack/react-query";
import { runAnalyticsTool } from "@/lib/api/analytics";
import { DatabaseEvidenceCard } from "@/components/analytics/database-evidence-card";
import { StatePanel } from "./state-panel";
import { Skeleton } from "@/components/ui/skeleton";
export function ToolEvidencePanel({
  tool,
  parameters = {},
  label,
}: {
  tool: string;
  parameters?: Record<string, unknown>;
  label: string;
}) {
  const query = useQuery({
    queryKey: ["analytics-tool", tool, parameters],
    queryFn: ({ signal }) => runAnalyticsTool(tool, parameters, signal),
    staleTime: 120_000,
  });
  if (query.isPending) return <Skeleton className="h-64" />;
  if (query.isError)
    return (
      <StatePanel
        kind="error"
        title={`${label} unavailable`}
        description="Check the backend and database, then retry."
      />
    );
  return <DatabaseEvidenceCard evidence={query.data} />;
}
