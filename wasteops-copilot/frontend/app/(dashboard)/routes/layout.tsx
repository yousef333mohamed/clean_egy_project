import { requireAnyPermission } from "@/lib/auth/guards";

export default async function RouteLayout({ children }: { children: React.ReactNode }) {
  await requireAnyPermission("optimization:request");
  return children;
}
