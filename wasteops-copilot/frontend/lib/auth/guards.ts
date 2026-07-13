import { notFound, redirect } from "next/navigation";
import { auth, authEnabled } from "@/auth";

export async function requireAnyPermission(...permissions: string[]) {
  if (!authEnabled) return null;
  const session = await auth();
  if (!session) redirect("/auth/signin");
  if (!permissions.some((permission) => session.user.permissions.includes(permission))) notFound();
  return session;
}
