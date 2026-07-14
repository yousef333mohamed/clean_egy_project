import type { ZodType } from "zod";
import { env } from "@/lib/env";
import { ApiError } from "@/lib/api/errors";

type RequestOptions<T> = Omit<RequestInit, "body"> & {
  body?: unknown;
  schema: ZodType<T>;
  timeoutMs?: number;
  safeRetry?: boolean;
};

function safeDetail(payload: unknown): string | undefined {
  if (!payload || typeof payload !== "object" || !("detail" in payload))
    return undefined;
  const detail = (payload as { detail?: unknown }).detail;
  return typeof detail === "string" && detail.length <= 500
    ? detail
    : undefined;
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions<T>,
): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(
    () => controller.abort(),
    options.timeoutMs ?? 20_000,
  );
  const abort = () => controller.abort();
  options.signal?.addEventListener("abort", abort, { once: true });
  const attempts = options.safeRetry ? 2 : 1;
  try {
    for (let attempt = 0; attempt < attempts; attempt += 1) {
      try {
        const baseUrl = env.NEXT_PUBLIC_AUTH_ENABLED ? "/api/backend" : env.NEXT_PUBLIC_API_BASE_URL;
        const backendPath = env.NEXT_PUBLIC_AUTH_ENABLED && path.startsWith("/api/") ? path.slice(4) : path;
        const response = await fetch(`${baseUrl}${backendPath}`, {
          ...options,
          body:
            options.body === undefined
              ? undefined
              : JSON.stringify(options.body),
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            ...options.headers,
          },
          signal: controller.signal,
        });
        const payload: unknown = await response.json().catch(() => null);
        const requestId =
          response.headers.get("x-request-id") ??
          (payload && typeof payload === "object" && "request_id" in payload
            ? String(payload.request_id)
            : undefined);
        if (!response.ok)
          throw new ApiError({
            status: response.status,
            message:
              safeDetail(payload) ?? `Request failed (${response.status})`,
            requestId,
          });
        const parsed = options.schema.safeParse(payload);
        if (!parsed.success) {
          if (env.NEXT_PUBLIC_APP_ENV === "development")
            console.error(
              "Backend response validation failed",
              parsed.error.issues,
            );
          throw new ApiError({
            status: 502,
            message: "The backend returned an invalid response shape.",
            requestId,
          });
        }
        return parsed.data;
      } catch (error) {
        if (
          error instanceof ApiError ||
          attempt + 1 >= attempts ||
          controller.signal.aborted
        )
          throw error;
      }
    }
    throw new ApiError({ status: 0, message: "Network request failed" });
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (controller.signal.aborted)
      throw new ApiError({
        status: 0,
        message: "The request was cancelled or timed out.",
      });
    throw new ApiError({
      status: 0,
      message: "The backend could not be reached.",
    });
  } finally {
    clearTimeout(timeout);
    options.signal?.removeEventListener("abort", abort);
  }
}

export const apiGet = <T>(
  path: string,
  schema: ZodType<T>,
  signal?: AbortSignal,
) => apiRequest(path, { method: "GET", schema, signal, safeRetry: true });
export const apiPost = <T>(
  path: string,
  body: unknown,
  schema: ZodType<T>,
  signal?: AbortSignal,
  timeoutMs?: number,
) => apiRequest(path, { method: "POST", body, schema, signal, timeoutMs });
