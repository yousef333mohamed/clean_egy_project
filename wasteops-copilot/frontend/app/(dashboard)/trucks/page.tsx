import Link from "next/link";
import { PageHeader } from "@/components/layout/page-header";
import { ToolEvidencePanel } from "@/components/shared/tool-evidence-panel";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
export default function TrucksPage() {
  return (
    <>
      <PageHeader
        title="Truck performance"
        description="Historical performance and transparent rule alerts. No result is presented as a machine-learning prediction."
        actions={
          <Button asChild>
            <Link href="/decisions">Request manager recommendation</Link>
          </Button>
        }
      />
      <div className="space-y-6">
        <ToolEvidencePanel
          tool="get_truck_performance_summary"
          label="Truck performance"
          parameters={{ latest_available: true }}
        />
        <section>
          <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold">
            Rule-based anomalies <Badge>Transparent rule-based alert</Badge>
          </h2>
          <ToolEvidencePanel
            tool="detect_truck_rule_anomalies"
            label="Truck rule alerts"
            parameters={{ latest_available: true }}
          />
        </section>
      </div>
    </>
  );
}
