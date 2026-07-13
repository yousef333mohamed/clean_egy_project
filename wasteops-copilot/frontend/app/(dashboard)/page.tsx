import { OperationalOverview } from "@/components/dashboard/operational-overview";
import { QuickActions } from "@/components/dashboard/quick-actions";
import { PageHeader } from "@/components/layout/page-header";
export default function OverviewPage() {
  return (
    <>
      <PageHeader
        title="Operations overview"
        description="Latest backend-supplied operational values. Sections may have different effective dates."
      />
      <OperationalOverview />
      <div className="mt-6">
        <QuickActions />
      </div>
    </>
  );
}
