import { z } from "zod";
import { apiGet } from "@/lib/api/client";
export const traceSchema = z.object({
  id: z.uuid(),
  request_id: z.string(),
  parent_trace_id: z.string().nullable(),
  trace_type: z.string(),
  route: z.string().nullable(),
  status: z.string(),
  started_at: z.string(),
  duration_ms: z.number().nullable(),
  provider: z.string().nullable(),
  model: z.string().nullable(),
  prompt_key: z.string().nullable(),
  prompt_version: z.string().nullable(),
  metrics: z.record(z.string(), z.unknown()),
  error_category: z.string().nullable(),
});
export const tracePageSchema = z.object({
  items: z.array(traceSchema),
  offset: z.number(),
  limit: z.number(),
});
export const getTraces = (signal?: AbortSignal) =>
  apiGet("/api/traces?limit=100", tracePageSchema, signal);
