import { requireAnyPermission } from "@/lib/auth/guards";

export default async function EvaluationAdminLayout({ children }: { children: React.ReactNode }) {
  await requireAnyPermission("evaluations:read");
  return children;
}
