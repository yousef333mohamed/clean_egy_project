import { apiPost } from "@/lib/api/client";
import { hybridResponseSchema, ragResponseSchema } from "@/lib/schemas/api";
export const askRag = (question: string, signal?: AbortSignal) =>
  apiPost("/api/chat/rag", { question }, ragResponseSchema, signal);
export const askHybrid = (question: string, signal?: AbortSignal) =>
  apiPost("/api/chat/hybrid", { question }, hybridResponseSchema, signal);
