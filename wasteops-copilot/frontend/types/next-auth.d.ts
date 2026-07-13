import "next-auth";
import "next-auth/jwt";

declare module "next-auth" {
  interface User {
    roles?: string[];
    permissions?: string[];
  }
  interface Session {
    user: {
      id: string;
      roles: string[];
      permissions: string[];
    } & Session["user"];
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
    accessTokenExpiresAt?: number;
    refreshToken?: string;
    roles?: string[];
    permissions?: string[];
  }
}
