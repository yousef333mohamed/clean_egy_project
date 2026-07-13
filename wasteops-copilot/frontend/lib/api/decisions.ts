import { z } from "zod";
import { apiGet, apiPost } from "@/lib/api/client";
import {
  decisionResponseSchema,
  previewResponseSchema,
} from "@/lib/schemas/api";
export const decisionTypesSchema = z.array(z.record(z.string(), z.unknown()));
export const getDecisionTypes = (signal?: AbortSignal) =>
  apiGet("/api/decisions/types", decisionTypesSchema, signal);
export const previewDecision = (request: unknown, signal?: AbortSignal) =>
  apiPost("/api/decisions/preview", request, previewResponseSchema, signal);
export const recommendDecision = (request: unknown, signal?: AbortSignal) =>
  apiPost("/api/decisions/recommend", request, decisionResponseSchema, signal);
