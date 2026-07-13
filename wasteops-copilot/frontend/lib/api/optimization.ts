import { z } from "zod";

import { apiPost } from "@/lib/api/client";

const stop = z.object({
  sequence: z.number(),
  bin_id: z.string(),
  arrival_minute: z.number(),
  estimated_load_kg: z.number(),
  cumulative_load_kg: z.number(),
  priority_score: z.number(),
  overflow_probability: z.number(),
});
const route = z.object({
  route_id: z.string(),
  truck_id: z.string(),
  required_workers: z.number(),
  stops: z.array(stop),
  estimated_distance_km: z.number(),
  estimated_duration_minutes: z.number(),
  estimated_load_kg: z.number(),
  estimated_fuel_liters: z.number(),
});
const summary = z.object({
  routes: z.array(route),
  unassigned_bin_ids: z.array(z.string()),
  total_distance_km: z.number(),
  total_duration_minutes: z.number(),
  total_load_kg: z.number(),
  total_fuel_liters: z.number(),
  objective_value: z.number(),
});
export const planSchema = z.object({
  plan_id: z.string(),
  status: z.enum(["FEASIBLE", "INFEASIBLE", "TIME_LIMIT"]),
  generated_at: z.string(),
  solver_name: z.string(),
  solver_version: z.string(),
  primary_plan: summary.nullable(),
  alternatives: z.array(z.object({ scenario: z.string(), summary })),
  warnings: z.array(z.string()),
  assumptions: z.array(z.string()),
  requires_human_approval: z.literal(true),
  executes_operations: z.literal(false),
});
export type RoutePlan = z.infer<typeof planSchema>;

export type PlanInput = {
  plan_date: string;
  bin_ids: string[];
  truck_ids: string[];
  depot: { latitude: number; longitude: number };
  workers_per_route: number;
  average_speed_kmh: number;
  traffic_multiplier: number;
  environmental_duration_multiplier: number;
};

export function previewPlan(input: PlanInput) {
  return apiPost("/api/optimization/plans/preview", input, planSchema);
}

const review = z.object({
  plan_id: z.string(),
  review_status: z.string(),
  executes_operations: z.literal(false),
  message: z.string(),
});
export function reviewPlan(planId: string, approved: boolean) {
  return apiPost(
    `/api/optimization/plans/${planId}/review`,
    {
      approved,
      review_notes: approved
        ? "Authorized manager reviewed constraints and approves this advisory plan."
        : "Authorized manager rejected this advisory plan for operational revision.",
    },
    review,
  );
}

const explanation = z.object({
  plan_id: z.string(),
  explanation: z.string(),
  evidence_id: z.literal("O1"),
  generated_by: z.enum(["llm", "deterministic"]),
  requires_human_approval: z.literal(true),
  executes_operations: z.literal(false),
});
export function explainPlan(planId: string) {
  return apiPost(`/api/optimization/plans/${planId}/explain`, {}, explanation);
}
