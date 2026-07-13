import { requireAnyPermission } from "@/lib/auth/guards";

export default async function PromptAdminLayout({ children }: { children: React.ReactNode }) {
  await requireAnyPermission("prompts:read");
  return children;
}
