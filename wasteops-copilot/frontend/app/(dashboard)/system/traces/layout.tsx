import { requireAnyPermission } from "@/lib/auth/guards";

export default async function TraceAdminLayout({ children }: { children: React.ReactNode }) {
  await requireAnyPermission("traces:read");
  return children;
}
