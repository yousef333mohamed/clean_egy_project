"use client";
import { useQuery } from "@tanstack/react-query";
import { Copy } from "lucide-react";
import { toast } from "sonner";
import { getTraces } from "@/lib/api/traces";
import { PageHeader } from "@/components/layout/page-header";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { StatePanel } from "@/components/shared/state-panel";
import { formatDate, formatDuration } from "@/lib/formatting";
export default function TracesPage() {
  const query = useQuery({
    queryKey: ["traces"],
    queryFn: ({ signal }) => getTraces(signal),
    staleTime: 30_000,
  });
  return (
    <>
      <PageHeader
        title="Safe interaction traces"
        description="Sanitized timing and routing summaries. Prompts, SQL, embeddings, credentials, documents, and complete model output are excluded."
      />
      {query.isPending ? (
        <Skeleton className="h-72" />
      ) : query.isError ? (
        <StatePanel
          kind="error"
          title="Trace API unavailable"
          description="The administrative API may be disabled."
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Request ID</TableHead>
              <TableHead>Type / route</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Duration</TableHead>
              <TableHead>Prompt version</TableHead>
              <TableHead>Timestamp</TableHead>
              <TableHead>Error</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {query.data.items.map((trace) => (
              <TableRow key={trace.id}>
                <TableCell>
                  <div className="flex items-center gap-1">
                    <code>{trace.request_id}</code>
                    <Button
                      variant="ghost"
                      size="icon"
                      aria-label="Copy request ID"
                      onClick={() =>
                        void navigator.clipboard
                          .writeText(trace.request_id)
                          .then(() => toast.success("Request ID copied"))
                      }
                    >
                      <Copy className="size-3" />
                    </Button>
                  </div>
                </TableCell>
                <TableCell>
                  {trace.trace_type}
                  <br />
                  <span className="text-muted-foreground text-xs">
                    {trace.route ?? "No route"}
                  </span>
                </TableCell>
                <TableCell>
                  <Badge>{trace.status}</Badge>
                </TableCell>
                <TableCell>{formatDuration(trace.duration_ms)}</TableCell>
                <TableCell>
                  {trace.prompt_key
                    ? `${trace.prompt_key} · ${trace.prompt_version ?? "unknown"}`
                    : "Not applicable"}
                </TableCell>
                <TableCell>{formatDate(trace.started_at)}</TableCell>
                <TableCell>{trace.error_category ?? "None"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </>
  );
}
