import { apiGet } from "@/lib/api/client";
import { healthSchema } from "@/lib/schemas/api";
export const getHealth = (signal?: AbortSignal) =>
  apiGet("/api/health", healthSchema, signal);
export const getDatabaseHealth = (signal?: AbortSignal) =>
  apiGet("/api/health/database", healthSchema, signal);
