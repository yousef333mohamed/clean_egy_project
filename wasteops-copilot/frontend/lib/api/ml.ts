import { z } from "zod";
import { apiGet, apiPost } from "@/lib/api/client";

const activeModelSchema = z.object({
  model_name: z.string(), version: z.string(), stage: z.string(), feature_version: z.string(),
  approval_status: z.string(), metrics: z.record(z.string(), z.number()),
  training_period: z.object({ start: z.string(), end: z.string() }),
});
export type ActiveModel = z.infer<typeof activeModelSchema>;

const monitoringSchema = z.object({ reports: z.array(z.record(z.string(), z.unknown())).default([]) }).passthrough();
const promotionSchema = z.object({ status: z.literal("REQUESTED"), model_name: z.string(), version: z.string(), target_stage: z.string(), executes_promotion: z.literal(false) });
const factorSchema = z.object({ feature: z.string(), direction: z.string(), contribution: z.number() });
const metadata = { model_name: z.string(), model_version: z.string(), prediction_timestamp: z.string(), feature_timestamp: z.string(), data_age_seconds: z.number(), warnings: z.array(z.string()) };
const overflowSchema = z.object({ ...metadata, bin_id: z.string(), horizon_hours: z.number(), overflow_probability: z.number().min(0).max(1), predicted_class: z.boolean(), decision_threshold: z.number(), risk_level: z.string(), top_factors: z.array(factorSchema) });
const prioritySchema = z.object({ ...metadata, bin_id: z.string(), priority_score: z.number().min(0).max(1), priority_level: z.string(), overflow_probability: z.number(), recommended_review_window_hours: z.number(), score_components: z.record(z.string(), z.number()), top_factors: z.array(factorSchema) });
const anomalySchema = z.object({ ...metadata, truck_id: z.string(), trip_date: z.string(), is_anomalous: z.boolean(), anomaly_score: z.number().min(0).max(1), severity: z.string(), triggered_rules: z.array(z.string()), model_factors: z.array(factorSchema), recommended_action_category: z.string() });

export const getActiveModels = (signal?: AbortSignal) => apiGet("/api/ml/models/active", z.array(activeModelSchema), signal);
export const getMonitoring = (kind: "drift" | "performance" | "data-quality", signal?: AbortSignal) => apiGet(`/api/ml/monitoring/${kind}`, monitoringSchema, signal);
export const requestPromotion = (model: ActiveModel) => apiPost(`/api/ml/models/${model.model_name}/promotion-requests`, { version: model.version, target_stage: "Production", reason: "Requested from protected model management for authorized registry review." }, promotionSchema);
export const predictBins = async (assetIds: string[], horizonHours: 6 | 12 | 24) => {
  const body = { asset_ids: assetIds, horizon_hours: horizonHours };
  const [overflow, priority] = await Promise.all([
    apiPost("/api/ml/predictions/bin-overflow", body, z.array(overflowSchema)),
    apiPost("/api/ml/predictions/collection-priority", body, z.array(prioritySchema)),
  ]);
  return { overflow, priority };
};
export const predictTrucks = (assetIds: string[]) => apiPost("/api/ml/predictions/truck-anomalies", { asset_ids: assetIds, horizon_hours: 24 }, z.array(anomalySchema));
