import { NextResponse, type NextRequest } from "next/server";
import { auth, authEnabled } from "@/auth";

const publicPaths = ["/auth/signin", "/auth/signout", "/auth/error", "/api/auth"];

type ProxyRequest = NextRequest & { auth?: unknown };

function securityResponse(request: ProxyRequest) {
  const path = request.nextUrl.pathname;
  if (authEnabled && !request.auth && !publicPaths.some((item) => path.startsWith(item))) {
    const destination = new URL("/auth/signin", request.url);
    destination.searchParams.set("callbackUrl", path.startsWith("/") ? path : "/");
    return NextResponse.redirect(destination);
  }
  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  const response = NextResponse.next({ request: { headers: requestHeaders } });
  const connectSources = new Set(["'self'"]);
  if (process.env.OIDC_ISSUER_URL) connectSources.add(new URL(process.env.OIDC_ISSUER_URL).origin);
  if (!authEnabled && process.env.NEXT_PUBLIC_API_BASE_URL) connectSources.add(new URL(process.env.NEXT_PUBLIC_API_BASE_URL).origin);
  const connect = [...connectSources].join(" ");
  response.headers.set(
    "Content-Security-Policy",
    `default-src 'self'; script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${process.env.NODE_ENV === "development" ? " 'unsafe-eval'" : ""}; style-src 'self' 'nonce-${nonce}'; img-src 'self' data:; font-src 'self'; connect-src ${connect}; frame-ancestors 'none'; base-uri 'self'; form-action 'self'`,
  );
  response.headers.set("x-content-type-options", "nosniff");
  response.headers.set("x-frame-options", "DENY");
  response.headers.set("referrer-policy", "strict-origin-when-cross-origin");
  response.headers.set("permissions-policy", "camera=(), microphone=(), geolocation=()")
  return response;
}

const authenticatedProxy = auth((request) => securityResponse(request));
export default authEnabled ? authenticatedProxy : securityResponse;

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
