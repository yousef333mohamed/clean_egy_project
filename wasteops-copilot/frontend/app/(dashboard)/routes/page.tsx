import { PageHeader } from "@/components/layout/page-header";
import { RoutePlanner } from "@/components/optimization/route-planner";
import { requireAnyPermission } from "@/lib/auth/guards";

export default async function RoutesPage() {
  const session = await requireAnyPermission("optimization:request");
  const canApprove = session ? session.user.permissions.includes("optimization:approve") : true;
  return (
    <>
      <PageHeader
        title="Route planning"
        description="OR-Tools collection plans with capacity, time, workforce, prediction, and availability constraints."
      />
      <RoutePlanner canApprove={canApprove} />
    </>
  );
}
