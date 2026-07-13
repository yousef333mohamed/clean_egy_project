import { z } from "zod";
import { apiGet, apiPost } from "@/lib/api/client";
export const promptKeySchema = z.object({
  prompt_key: z.string(),
  active_version: z.string().nullable(),
  source: z.string(),
});
export const promptVersionSchema = z.object({
  id: z.uuid(),
  prompt_key: z.string(),
  version: z.string(),
  content_hash: z.string(),
  description: z.string().nullable(),
  status: z.string(),
  created_by: z.string().nullable(),
  created_at: z.string(),
  activated_at: z.string().nullable(),
  deactivated_at: z.string().nullable(),
});
export const getPrompts = (signal?: AbortSignal) =>
  apiGet("/api/prompts", z.array(promptKeySchema), signal);
export const getPromptVersions = (key: string, signal?: AbortSignal) =>
  apiGet(
    `/api/prompts/${encodeURIComponent(key)}/versions`,
    z.array(promptVersionSchema),
    signal,
  );
export const createPrompt = (
  key: string,
  body: unknown,
  signal?: AbortSignal,
) =>
  apiPost(
    `/api/prompts/${encodeURIComponent(key)}/versions`,
    body,
    promptVersionSchema,
    signal,
  );
export const activatePrompt = (
  key: string,
  version: string,
  signal?: AbortSignal,
) =>
  apiPost(
    `/api/prompts/${encodeURIComponent(key)}/versions/${encodeURIComponent(version)}/activate`,
    {},
    promptVersionSchema,
    signal,
  );
export const archivePrompt = (
  key: string,
  version: string,
  signal?: AbortSignal,
) =>
  apiPost(
    `/api/prompts/${encodeURIComponent(key)}/versions/${encodeURIComponent(version)}/archive`,
    {},
    promptVersionSchema,
    signal,
  );
