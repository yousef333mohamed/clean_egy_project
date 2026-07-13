"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { predictBins, predictTrucks } from "@/lib/api/ml";
import { userErrorMessage } from "@/lib/api/errors";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export function PredictionPanel({ domain }: { domain: "bins" | "trucks" }) {
  const [ids, setIds] = useState("");
  const mutation = useMutation({
    mutationFn: async () => {
      const assets = ids.split(",").map((item) => item.trim()).filter(Boolean);
      if (!assets.length) throw new Error("Enter at least one asset ID.");
      return domain === "bins" ? predictBins(assets, 24) : predictTrucks(assets);
    },
    onError: (error) => toast.error(error instanceof Error && error.message.startsWith("Enter") ? error.message : userErrorMessage(error)),
  });
  type DisplayRow = { id: string; label: string; value: string; secondary: string; version: string; timestamp: string; freshness: string; factors: { feature: string; direction: string; contribution: number }[]; warnings: string[] };
  let rows: DisplayRow[] = [];
  if (mutation.data) {
    const data = mutation.data;
    if ("overflow" in data) {
      rows = data.overflow.map((overflow) => ({
        id: overflow.bin_id, label: "Prediction", value: `${(overflow.overflow_probability * 100).toFixed(1)}% overflow probability`,
        secondary: `${(data.priority.find((item) => item.bin_id === overflow.bin_id)?.priority_score ?? 0).toFixed(2)} collection priority`,
        version: overflow.model_version, timestamp: overflow.prediction_timestamp, freshness: `${overflow.data_age_seconds}s old`, factors: overflow.top_factors, warnings: overflow.warnings,
      }));
    } else {
      rows = data.map((item) => ({ id: item.truck_id, label: "ML-detected anomaly", value: item.anomaly_score.toFixed(2), secondary: item.is_anomalous ? item.severity : "Not flagged", version: item.model_version, timestamp: item.prediction_timestamp, freshness: `${item.data_age_seconds}s old`, factors: item.model_factors, warnings: item.warnings }));
    }
  }
  return <Card><CardHeader><CardTitle>{domain === "bins" ? "Overflow and collection-priority predictions" : "ML anomaly predictions"}</CardTitle></CardHeader><CardContent className="space-y-4">
    <div className="flex gap-2"><Input value={ids} onChange={(event) => setIds(event.target.value)} placeholder={domain === "bins" ? "BIN-001, BIN-002" : "TRK-001"} aria-label="Comma-separated asset IDs" /><Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>{mutation.isPending ? "Predicting…" : "Request prediction"}</Button></div>
    <p className="text-muted-foreground text-xs">Predictions are advisory, may be stale or unavailable, and never execute an operational action. Probability is not Decision Intelligence confidence.</p>
    {rows.map((row) => <div key={row.id} className="border-border rounded-lg border p-4"><div className="flex flex-wrap items-center gap-2"><strong>{row.id}</strong><Badge>{row.label}</Badge><span>{row.value}</span><span className="text-muted-foreground">{row.secondary}</span></div><p className="text-muted-foreground mt-2 text-xs">Model {row.version} · {row.freshness} · predicted {new Date(row.timestamp).toLocaleString()}</p>{row.factors.length > 0 && <p className="mt-2 text-sm">Top associated factors: {row.factors.map((factor) => `${factor.feature} (${factor.direction})`).join(", ")}. These are not causal claims.</p>}{row.warnings.map((warning) => <p key={warning} className="mt-1 text-sm text-amber-700 dark:text-amber-300">{warning}</p>)}</div>)}
  </CardContent></Card>;
}
