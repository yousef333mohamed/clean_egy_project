import { AppHeader } from "@/components/layout/app-header";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { auth, authEnabled } from "@/auth";
import { redirect } from "next/navigation";
export const dynamic = "force-dynamic";
export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = authEnabled ? await auth() : null;
  if (authEnabled && !session) redirect("/auth/signin");
  const permissions = session?.user.permissions;
  return (
    <div className="min-h-dvh">
      <div className="fixed inset-y-0 start-0 hidden lg:block">
        <AppSidebar permissions={permissions} />
      </div>
      <div className="lg:ps-64">
        <AppHeader displayName={session?.user.name ?? session?.user.email ?? undefined} permissions={permissions} />
        <main
          id="main-content"
          className="mx-auto max-w-[1600px] p-4 md:p-6 lg:p-8"
        >
          {children}
        </main>
      </div>
    </div>
  );
}
