import { afterEach, describe, expect, it, vi } from "vitest";
import { z } from "zod";
import { apiRequest } from "@/lib/api/client";

afterEach(() => vi.unstubAllGlobals());
describe("API client", () => {
  it("maps backend errors without exposing raw payloads", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Unavailable" }), {
          status: 503,
          headers: {
            "content-type": "application/json",
            "x-request-id": "req-1",
          },
        }),
      ),
    );
    await expect(
      apiRequest("/api/test", {
        method: "GET",
        schema: z.object({ ok: z.boolean() }),
      }),
    ).rejects.toMatchObject({ status: 503, requestId: "req-1" });
  });
  it("fails closed when response validation fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response(JSON.stringify({ bad: true }), { status: 200 }),
        ),
    );
    await expect(
      apiRequest("/api/test", {
        method: "GET",
        schema: z.object({ ok: z.boolean() }),
      }),
    ).rejects.toMatchObject({ status: 502 });
  });
  it("supports cancellation", async () => {
    const controller = new AbortController();
    controller.abort();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new DOMException("aborted", "AbortError")),
    );
    await expect(
      apiRequest("/api/test", {
        method: "GET",
        schema: z.any(),
        signal: controller.signal,
      }),
    ).rejects.toMatchObject({ status: 0 });
  });
});
