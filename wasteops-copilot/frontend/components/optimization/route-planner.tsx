"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  explainPlan,
  previewPlan,
  reviewPlan,
  type RoutePlan,
} from "@/lib/api/optimization";
import { userErrorMessage } from "@/lib/api/errors";

const ids = (value: string) => value.split(",").map((item) => item.trim()).filter(Boolean);

export function RoutePlanner({ canApprove }: { canApprove: boolean }) {
  const [bins, setBins] = useState("");
  const [trucks, setTrucks] = useState("");
  const [planDate, setPlanDate] = useState(new Date().toISOString().slice(0, 10));
  const [latitude, setLatitude] = useState("30.0444");
  const [longitude, setLongitude] = useState("31.2357");
  const [plan, setPlan] = useState<RoutePlan>();
  const [explanation, setExplanation] = useState("");
  const [reviewed, setReviewed] = useState(false);

  const mutation = useMutation({
    mutationFn: () =>
      previewPlan({
        plan_date: planDate,
        bin_ids: ids(bins),
        truck_ids: ids(trucks),
        depot: { latitude: Number(latitude), longitude: Number(longitude) },
        workers_per_route: 2,
        average_speed_kmh: 25,
        traffic_multiplier: 1,
        environmental_duration_multiplier: 1,
      }),
    onSuccess: (value) => {
      setPlan(value);
      setExplanation("");
      setReviewed(false);
    },
    onError: (error) => toast.error(userErrorMessage(error)),
  });
  const review = useMutation({
    mutationFn: (approved: boolean) => reviewPlan(plan!.plan_id, approved),
    onSuccess: (value) => {
      setReviewed(true);
      toast.success(value.message);
    },
    onError: (error) => toast.error(userErrorMessage(error)),
  });
  const explain = useMutation({
    mutationFn: () => explainPlan(plan!.plan_id),
    onSuccess: (value) => setExplanation(value.explanation),
    onError: (error) => toast.error(userErrorMessage(error)),
  });

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><CardTitle>Generate advisory collection plan</CardTitle></CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2">
          <Input value={bins} onChange={(event) => setBins(event.target.value)} placeholder="BIN-001, BIN-002" aria-label="Bin IDs" />
          <Input value={trucks} onChange={(event) => setTrucks(event.target.value)} placeholder="TRK-001, TRK-002" aria-label="Truck IDs" />
          <Input type="date" value={planDate} onChange={(event) => setPlanDate(event.target.value)} aria-label="Plan date" />
          <div className="grid grid-cols-2 gap-2">
            <Input type="number" value={latitude} onChange={(event) => setLatitude(event.target.value)} aria-label="Depot latitude" />
            <Input type="number" value={longitude} onChange={(event) => setLongitude(event.target.value)} aria-label="Depot longitude" />
          </div>
          <Button disabled={mutation.isPending || !bins || !trucks} onClick={() => mutation.mutate()}>
            {mutation.isPending ? "Optimizing…" : "Generate plan"}
          </Button>
          <p className="text-muted-foreground text-xs">Predictions and operational records supply scores, loads, capacity, workforce, and availability. OR-Tools calculates routes; the browser does not.</p>
        </CardContent>
      </Card>
      {plan && (
        <>
          <Card>
            <CardHeader>
              <div className="flex flex-wrap gap-2"><CardTitle>Plan {plan.plan_id}</CardTitle><Badge>{plan.status}</Badge><Badge>Manager approval required</Badge></div>
            </CardHeader>
            <CardContent className="space-y-4">
              {plan.primary_plan?.routes.map((route) => (
                <div className="rounded-lg border p-4" key={route.route_id}>
                  <h3 className="font-semibold">{route.route_id} · {route.truck_id}</h3>
                  <p className="text-sm">{route.estimated_distance_km} km · {route.estimated_duration_minutes} min · {route.estimated_load_kg} kg · {route.estimated_fuel_liters} L · {route.required_workers} workers</p>
                  <ol className="mt-2 list-inside list-decimal text-sm">
                    {route.stops.map((stop) => <li key={stop.bin_id}>{stop.bin_id} — priority {stop.priority_score.toFixed(2)}, overflow {(stop.overflow_probability * 100).toFixed(1)}%</li>)}
                  </ol>
                </div>
              ))}
              {plan.warnings.map((warning) => <p className="text-amber-700" key={warning}>{warning}</p>)}
              {plan.assumptions.map((assumption) => <p className="text-muted-foreground text-xs" key={assumption}>{assumption}</p>)}
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Alternative scenarios</CardTitle></CardHeader>
            <CardContent>{plan.alternatives.length ? plan.alternatives.map((alternative) => <p key={alternative.scenario}>{alternative.scenario}: {alternative.summary.routes.length} routes, {alternative.summary.unassigned_bin_ids.length} unassigned bins</p>) : <p className="text-muted-foreground text-sm">No feasible alternative was found within the configured solve limit.</p>}</CardContent>
          </Card>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => explain.mutate()} disabled={explain.isPending}>{explain.isPending ? "Explaining…" : "Explain plan"}</Button>
            {canApprove && <Button onClick={() => review.mutate(true)} disabled={review.isPending || reviewed}>Approve advisory plan</Button>}
            {canApprove && <Button variant="outline" onClick={() => review.mutate(false)} disabled={review.isPending || reviewed}>Reject plan</Button>}
          </div>
          {explanation && <Card><CardHeader><CardTitle>Grounded plan explanation</CardTitle></CardHeader><CardContent><p className="whitespace-pre-wrap text-sm">{explanation}</p></CardContent></Card>}
          <p className="text-muted-foreground text-sm">{canApprove ? "Approval records a review only. It does not dispatch trucks, assign workers, or modify an operational schedule." : "An authorized operations manager must approve or reject this plan before execution."}</p>
        </>
      )}
    </div>
  );
}
