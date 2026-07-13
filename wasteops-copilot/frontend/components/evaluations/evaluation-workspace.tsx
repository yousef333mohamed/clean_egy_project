"use client";
import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  getEvaluationDatasets,
  getQualityGate,
  startEvaluation,
} from "@/lib/api/evaluation";
import { userErrorMessage } from "@/lib/api/errors";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { StatePanel } from "@/components/shared/state-panel";
export function EvaluationWorkspace() {
  const datasets = useQuery({
    queryKey: ["evaluation-datasets"],
    queryFn: ({ signal }) => getEvaluationDatasets(signal),
    staleTime: 300_000,
  });
  const [runId, setRunId] = useState<string>();
  const mutation = useMutation({
    mutationFn: (dataset: string) => startEvaluation(dataset),
    onSuccess: (data) => setRunId(data.run_id),
    onError: (e) => toast.error(userErrorMessage(e)),
  });
  const gate = useQuery({
    queryKey: ["quality-gate", runId],
    queryFn: ({ signal }) => getQualityGate(runId!, signal),
    enabled: Boolean(runId),
    staleTime: 10_000,
  });
  if (datasets.isPending) return <Skeleton className="h-48" />;
  if (datasets.isError)
    return (
      <StatePanel
        kind="error"
        title="Evaluation API unavailable"
        description="This administrative feature may be disabled. Frontend flags are not authorization controls."
      />
    );
  return (
    <div className="space-y-6">
      <div className="grid gap-3 md:grid-cols-2">
        {datasets.data.map((dataset) => (
          <Card key={dataset.name}>
            <CardHeader>
              <CardTitle>{dataset.name}</CardTitle>
              <div className="flex gap-2">
                <Badge>{dataset.type}</Badge>
                <Badge>v{dataset.version}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <Button
                disabled={mutation.isPending}
                onClick={() => mutation.mutate(dataset.name)}
              >
                {mutation.isPending
                  ? "Evaluation pending…"
                  : "Run with fake providers"}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
      {gate.isSuccess && (
        <Card
          className={
            gate.data.passed ? "border-emerald-400" : "border-destructive"
          }
        >
          <CardHeader>
            <CardTitle>
              Quality gate{" "}
              <Badge>{gate.data.passed ? "Passed" : "Failed"}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-3 text-sm">
              Critical failures: {gate.data.critical_failures}
            </p>
            <div className="grid gap-2 sm:grid-cols-2">
              {Object.entries(gate.data.metrics).map(([name, value]) => (
                <div
                  key={name}
                  className="bg-muted flex justify-between rounded-lg p-3 text-sm"
                >
                  <span>{name.replaceAll("_", " ")}</span>
                  <span className="font-medium tabular-nums">{value}</span>
                </div>
              ))}
            </div>
            <p className="text-muted-foreground mt-4 text-xs">
              Pass/fail values come directly from the deterministic backend
              quality gate.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
