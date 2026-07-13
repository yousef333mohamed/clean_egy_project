import NextAuth from "next-auth";
import type { OAuthConfig } from "next-auth/providers";
import type { JWT } from "next-auth/jwt";

type WasteOpsProfile = {
  sub: string;
  name?: string;
  email?: string;
  picture?: string;
  roles?: unknown;
  permissions?: unknown;
};

const strings = (value: unknown): string[] =>
  Array.isArray(value) && value.every((item) => typeof item === "string")
    ? value
    : [];

const oidcProvider: OAuthConfig<WasteOpsProfile> = {
  id: "oidc",
  name: "Organization identity provider",
  type: "oidc",
  issuer: process.env.OIDC_ISSUER_URL,
  clientId: process.env.OIDC_CLIENT_ID,
  clientSecret: process.env.OIDC_CLIENT_SECRET,
  checks: ["pkce", "state"],
  authorization: {
    params: {
      scope: "openid profile email offline_access",
      audience: process.env.OIDC_AUDIENCE ?? "wasteops-api",
    },
  },
  profile(profile) {
    return {
      id: profile.sub,
      name: profile.name,
      email: profile.email,
      image: profile.picture,
      roles: strings(profile.roles),
      permissions: strings(profile.permissions),
    };
  },
};

export const authEnabled = process.env.AUTH_ENABLED === "true";
if (authEnabled && (!process.env.OIDC_ISSUER_URL?.startsWith("https://") || !process.env.OIDC_CLIENT_ID || !process.env.OIDC_CLIENT_SECRET || !process.env.AUTH_SECRET)) {
  throw new Error("Secure OIDC and Auth.js configuration is required when AUTH_ENABLED=true");
}

export async function refreshAccessToken(token: JWT): Promise<JWT> {
  if (!token.refreshToken || !process.env.OIDC_ISSUER_URL || !process.env.OIDC_CLIENT_ID || !process.env.OIDC_CLIENT_SECRET) {
    return { ...token, accessToken: undefined, refreshToken: undefined };
  }
  try {
    const discovery = await fetch(`${process.env.OIDC_ISSUER_URL.replace(/\/$/, "")}/.well-known/openid-configuration`, { signal: AbortSignal.timeout(10_000) });
    const metadata = (await discovery.json()) as { token_endpoint?: unknown };
    if (!discovery.ok || typeof metadata.token_endpoint !== "string" || new URL(metadata.token_endpoint).protocol !== "https:") throw new Error("Invalid OIDC metadata");
    const response = await fetch(metadata.token_endpoint, {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ grant_type: "refresh_token", refresh_token: token.refreshToken, client_id: process.env.OIDC_CLIENT_ID, client_secret: process.env.OIDC_CLIENT_SECRET }),
      signal: AbortSignal.timeout(10_000),
    });
    const refreshed = (await response.json()) as { access_token?: unknown; refresh_token?: unknown; expires_in?: unknown };
    if (!response.ok || typeof refreshed.access_token !== "string") throw new Error("OIDC refresh rejected");
    return {
      ...token,
      accessToken: refreshed.access_token,
      refreshToken: typeof refreshed.refresh_token === "string" ? refreshed.refresh_token : token.refreshToken,
      accessTokenExpiresAt: Math.floor(Date.now() / 1000) + (typeof refreshed.expires_in === "number" ? refreshed.expires_in : 300),
    };
  } catch {
    return { ...token, accessToken: undefined, refreshToken: undefined };
  }
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: authEnabled ? [oidcProvider] : [],
  session: { strategy: "jwt", maxAge: 60 * 60 * 8 },
  pages: { signIn: "/auth/signin", signOut: "/auth/signout", error: "/auth/error" },
  callbacks: {
    async jwt({ token, account, user }) {
      if (account?.access_token) {
        token.accessToken = account.access_token;
        token.accessTokenExpiresAt = account.expires_at;
        token.refreshToken = account.refresh_token;
      }
      if (user) {
        token.roles = strings(user.roles);
        token.permissions = strings(user.permissions);
      }
      if (typeof token.accessTokenExpiresAt === "number" && Date.now() < (token.accessTokenExpiresAt - 60) * 1000) return token;
      if (token.refreshToken) return refreshAccessToken(token);
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.sub ?? "";
        session.user.roles = strings(token.roles);
        session.user.permissions = strings(token.permissions);
      }
      // Access and refresh tokens remain only in the encrypted HTTP-only Auth.js cookie.
      return session;
    },
    async redirect({ url, baseUrl }) {
      if (url.startsWith("/")) return `${baseUrl}${url}`;
      try {
        return new URL(url).origin === baseUrl ? url : baseUrl;
      } catch {
        return baseUrl;
      }
    },
  },
  cookies: {
    sessionToken: {
      name: `${process.env.NODE_ENV === "production" ? "__Secure-" : ""}wasteops.session-token`,
      options: {
        httpOnly: true,
        sameSite: "lax",
        path: "/",
        secure: process.env.NODE_ENV === "production",
      },
    },
  },
  trustHost: process.env.AUTH_TRUST_HOST === "true",
});
