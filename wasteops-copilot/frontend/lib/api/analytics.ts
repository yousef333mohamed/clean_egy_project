import { apiPost } from "@/lib/api/client";
import { analyticsResponseSchema, evidenceSchema } from "@/lib/schemas/api";

const GENERATED_ANSWER_TIMEOUT_MS = 120_000;

export const queryAnalytics = (question: string, signal?: AbortSignal) =>
  apiPost(
    "/api/analytics/query",
    { question },
    analyticsResponseSchema,
    signal,
    GENERATED_ANSWER_TIMEOUT_MS,
  );
export const getOperationalOverview = (signal?: AbortSignal) =>
  apiPost(
    "/api/analytics/tools/get_operational_overview",
    { latest_available: true },
    evidenceSchema,
    signal,
  );
export const runAnalyticsTool = (
  tool: string,
  parameters: Record<string, unknown>,
  signal?: AbortSignal,
) =>
  apiPost(
    `/api/analytics/tools/${encodeURIComponent(tool)}`,
    parameters,
    evidenceSchema,
    signal,
  );
