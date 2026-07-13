import { AppHeader } from "@/components/layout/app-header";
import { AppSidebar } from "@/components/layout/app-sidebar";
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-dvh">
      <div className="fixed inset-y-0 start-0 hidden lg:block">
        <AppSidebar />
      </div>
      <div className="lg:ps-64">
        <AppHeader />
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
