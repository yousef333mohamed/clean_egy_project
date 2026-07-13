import { getToken } from "next-auth/jwt";
import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { authEnabled, refreshAccessToken } from "@/auth";

const allowedRoots = new Set([
  "analytics", "audit", "auth", "chat", "decisions", "documents", "evaluation",
  "feedback", "health", "ingestion", "jobs", "prompts", "retrieval", "traces",
]);
const mutating = new Set(["POST", "PUT", "PATCH", "DELETE"]);

async function forward(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  if (!path.length || !allowedRoots.has(path[0]) || path.some((part) => !/^[A-Za-z0-9_.-]+$/.test(part) || part === "..")) {
    return NextResponse.json({ detail: "Route not allowed" }, { status: 404 });
  }
  if (mutating.has(request.method) && request.headers.get("origin") !== request.nextUrl.origin) {
    return NextResponse.json({ detail: "Origin check failed" }, { status: 403 });
  }
  const backend = process.env.BACKEND_INTERNAL_URL;
  if (!backend) return NextResponse.json({ detail: "Backend is not configured" }, { status: 503 });
  let accessToken: string | undefined;
  if (authEnabled) {
    const token = await getToken({ req: request, secret: process.env.AUTH_SECRET, secureCookie: process.env.NODE_ENV === "production", cookieName: `${process.env.NODE_ENV === "production" ? "__Secure-" : ""}wasteops.session-token` });
    const effectiveToken = token && typeof token.accessTokenExpiresAt === "number" && Date.now() >= (token.accessTokenExpiresAt - 60) * 1000 ? await refreshAccessToken(token) : token;
    accessToken = typeof effectiveToken?.accessToken === "string" ? effectiveToken.accessToken : undefined;
    if (!accessToken) return NextResponse.json({ detail: "Authentication required" }, { status: 401 });
  }
  const target = new URL(`/api/${path.join("/")}`, backend);
  target.search = request.nextUrl.search;
  const requestId = request.headers.get("x-request-id");
  const headers = new Headers({ accept: "application/json" });
  if (requestId && /^[A-Za-z0-9._-]{1,64}$/.test(requestId)) headers.set("x-request-id", requestId);
  if (accessToken) headers.set("authorization", `Bearer ${accessToken}`);
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  const body = mutating.has(request.method) ? await request.arrayBuffer() : undefined;
  if (body && body.byteLength > 10_485_760) return NextResponse.json({ detail: "Request body too large" }, { status: 413 });
  const upstream = await fetch(target, { method: request.method, headers, body, redirect: "manual", signal: AbortSignal.timeout(120_000) });
  const responseHeaders = new Headers({ "content-type": upstream.headers.get("content-type") ?? "application/json" });
  const upstreamRequestId = upstream.headers.get("x-request-id");
  if (upstreamRequestId) responseHeaders.set("x-request-id", upstreamRequestId);
  return new NextResponse(upstream.body, { status: upstream.status, headers: responseHeaders });
}

export const GET = forward;
export const POST = forward;
export const PUT = forward;
export const PATCH = forward;
export const DELETE = forward;
