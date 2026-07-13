"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { getActiveModels, getMonitoring, requestPromotion, type ActiveModel } from "@/lib/api/ml";
import { userErrorMessage } from "@/lib/api/errors";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatePanel } from "@/components/shared/state-panel";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export function ModelManagement() {
  const models = useQuery({ queryKey: ["ml-models"], queryFn: ({ signal }) => getActiveModels(signal), staleTime: 60_000 });
  const drift = useQuery({ queryKey: ["ml-drift"], queryFn: ({ signal }) => getMonitoring("drift", signal), staleTime: 60_000 });
  const promotion = useMutation({
    mutationFn: (model: ActiveModel) => requestPromotion(model),
    onSuccess: () => toast.success("Promotion review requested. No model was promoted automatically."),
    onError: (error) => toast.error(userErrorMessage(error)),
  });
  if (models.isPending) return <Skeleton className="h-64" />;
  if (models.isError) return <StatePanel kind="error" title="Model service unavailable" description="Historical analytics and document guidance remain available. Predictive model state cannot currently be verified." />;
  return <div className="space-y-6">
    <div className="grid gap-4 md:grid-cols-3">
      <Card><CardHeader><CardTitle>Prediction overview</CardTitle></CardHeader><CardContent><p className="text-3xl font-semibold">{models.data.length}</p><p className="text-muted-foreground text-sm">approved active model records</p></CardContent></Card>
      <Card><CardHeader><CardTitle>Model health</CardTitle></CardHeader><CardContent><Badge>{models.data.every((item) => item.stage === "Production") ? "Production metadata available" : "Review required"}</Badge></CardContent></Card>
      <Card><CardHeader><CardTitle>Drift monitoring</CardTitle></CardHeader><CardContent><p className="text-3xl font-semibold">{drift.data?.reports.length ?? 0}</p><p className="text-muted-foreground text-sm">recent reports; drift is a review signal, not proof of failure</p></CardContent></Card>
    </div>
    <Card><CardHeader><CardTitle>Registered production models</CardTitle></CardHeader><CardContent>
      {models.data.length === 0 ? <StatePanel kind="empty" title="No active production models" description="Predictions may be unavailable or explicitly marked as baseline fallbacks. A model card and approved promotion are required." /> :
      <Table><TableHeader><TableRow><TableHead>Model</TableHead><TableHead>Version</TableHead><TableHead>Stage</TableHead><TableHead>Training period</TableHead><TableHead>Feature version</TableHead><TableHead>Approval</TableHead><TableHead>Action</TableHead></TableRow></TableHeader><TableBody>{models.data.map((model) => <TableRow key={`${model.model_name}:${model.version}`}><TableCell className="font-medium">{model.model_name}</TableCell><TableCell>{model.version}</TableCell><TableCell><Badge>{model.stage}</Badge></TableCell><TableCell>{model.training_period.start} — {model.training_period.end}</TableCell><TableCell>{model.feature_version}</TableCell><TableCell>{model.approval_status}</TableCell><TableCell><Button size="sm" variant="outline" disabled={promotion.isPending} onClick={() => promotion.mutate(model)}>Request promotion review</Button></TableCell></TableRow>)}</TableBody></Table>}
    </CardContent></Card>
    <p className="text-muted-foreground text-sm">Predictions are not guaranteed outcomes. Probability is not Decision Intelligence confidence. Requests do not promote models; backend quality gates and explicit human approval remain mandatory.</p>
  </div>;
}
