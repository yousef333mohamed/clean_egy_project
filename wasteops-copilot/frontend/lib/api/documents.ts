import { z } from "zod";
import { apiGet, apiPost } from "@/lib/api/client";
import { documentPageSchema } from "@/lib/schemas/api";
export const discoveredDocumentSchema = z.object({
  filename: z.string(),
  relative_path: z.string(),
  extension: z.string(),
  size_bytes: z.number(),
  modified_at: z.string(),
  supported: z.boolean(),
  rejection_reason: z.string().nullable(),
});
export const getDocuments = (signal?: AbortSignal) =>
  apiGet("/api/documents?limit=100", documentPageSchema, signal);
export const getDocumentFiles = (signal?: AbortSignal) =>
  apiGet("/api/documents/files", z.array(discoveredDocumentSchema), signal);
export const validateDocument = (relativePath: string, signal?: AbortSignal) =>
  apiPost(
    "/api/documents/validate",
    { relative_path: relativePath },
    z.record(z.string(), z.unknown()),
    signal,
  );
export const ingestDocument = (relativePath: string, signal?: AbortSignal) =>
  apiPost(
    "/api/documents/ingest",
    { relative_path: relativePath },
    z.record(z.string(), z.unknown()),
    signal,
  );
