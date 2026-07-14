import { apiPost } from "@/lib/api/client";
import { hybridResponseSchema, ragResponseSchema } from "@/lib/schemas/api";

const GENERATED_ANSWER_TIMEOUT_MS = 120_000;

export const askRag = (question: string, signal?: AbortSignal) =>
  apiPost("/api/chat/rag", { question }, ragResponseSchema, signal, GENERATED_ANSWER_TIMEOUT_MS);
export const askHybrid = (question: string, signal?: AbortSignal) =>
  apiPost("/api/chat/hybrid", { question }, hybridResponseSchema, signal, GENERATED_ANSWER_TIMEOUT_MS);
