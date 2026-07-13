import { z } from "zod";
import { apiGet, apiPost } from "@/lib/api/client";
import { evaluationRunStartSchema } from "@/lib/schemas/api";
export const datasetSchema = z.object({
  name: z.string(),
  type: z.string(),
  path: z.string(),
  version: z.string(),
});
export const getEvaluationDatasets = (signal?: AbortSignal) =>
  apiGet("/api/evaluation/datasets", z.array(datasetSchema), signal);
export const startEvaluation = (dataset: string, signal?: AbortSignal) =>
  apiPost(
    "/api/evaluation/runs",
    { dataset, mode: "FAKE_PROVIDERS" },
    evaluationRunStartSchema,
    signal,
  );
export const qualityGateSchema = z.object({
  passed: z.boolean(),
  metrics: z.record(z.string(), z.number()),
  failed_rules: z.array(z.record(z.string(), z.unknown())),
  critical_failures: z.number(),
});
export const getQualityGate = (id: string, signal?: AbortSignal) =>
  apiGet(
    `/api/evaluation/runs/${encodeURIComponent(id)}/quality-gate`,
    qualityGateSchema,
    signal,
  );
