import { z } from "zod";
import { apiGet, apiPost } from "@/lib/api/client";
import { ingestionResultSchema } from "@/lib/schemas/api";
export const discoveredFileSchema = z.object({
  dataset: z.string(),
  filename: z.string().nullable(),
  size_bytes: z.number().nullable(),
  available: z.boolean(),
});
export const getIngestionFiles = (signal?: AbortSignal) =>
  apiGet("/api/ingestion/files", z.array(discoveredFileSchema), signal);
export const validateDataset = (dataset: string, signal?: AbortSignal) =>
  apiPost(
    `/api/ingestion/validate/${encodeURIComponent(dataset)}`,
    { force: false },
    ingestionResultSchema,
    signal,
  );
export const ingestDataset = (dataset: string, signal?: AbortSignal) =>
  apiPost(
    `/api/ingestion/csv/${encodeURIComponent(dataset)}`,
    { force: false },
    ingestionResultSchema,
    signal,
  );
