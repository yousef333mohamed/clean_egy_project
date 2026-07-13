import { requireAnyPermission } from "@/lib/auth/guards";

export default async function IngestionAdminLayout({ children }: { children: React.ReactNode }) {
  await requireAnyPermission("datasets:read", "documents:ingest");
  return children;
}
