import { requireAnyPermission } from "@/lib/auth/guards";

export default async function ModelAdminLayout({ children }: { children: React.ReactNode }) {
  await requireAnyPermission("system:configure");
  return children;
}
