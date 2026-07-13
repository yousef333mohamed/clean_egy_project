import { apiGet } from "@/lib/api/client";
import { healthSchema, versionSchema } from "@/lib/schemas/api";
export const getHealth = (signal?: AbortSignal) =>
  apiGet("/api/health", healthSchema, signal);
export const getDatabaseHealth = (signal?: AbortSignal) =>
  apiGet("/api/health/database", healthSchema, signal);
export const getVersion = (signal?: AbortSignal) =>
  apiGet("/api/health/version", versionSchema, signal);
