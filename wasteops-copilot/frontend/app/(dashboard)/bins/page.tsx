"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { PageHeader } from "@/components/layout/page-header";
import { ToolEvidencePanel } from "@/components/shared/tool-evidence-panel";
import { Button } from "@/components/ui/button";
const tabs = {
  critical: ["Critical Fill", "list_critical_bins"],
  battery: ["Low Battery", "list_low_battery_bins"],
  sensors: ["Sensor Faults", "list_sensor_fault_bins"],
} as const;
export default function BinsPage() {
  const search = useSearchParams();
  const selected = (search.get("tab") ?? "critical") as keyof typeof tabs;
  const active = tabs[selected] ?? tabs.critical;
  return (
    <>
      <PageHeader
        title="Smart bins"
        description="Latest-state bin alerts from transparent configured backend rules. Historical faults are not presented as current faults."
      />
      <div className="mb-5 flex flex-wrap gap-2" role="tablist">
        {Object.entries(tabs).map(([key, [label]]) => (
          <Button
            asChild
            key={key}
            variant={key === selected ? "default" : "outline"}
          >
            <Link
              role="tab"
              aria-selected={key === selected}
              href={`/bins?tab=${key}`}
            >
              {label}
            </Link>
          </Button>
        ))}
      </div>
      <p className="text-muted-foreground mb-4 text-sm">
        Critical fill and low-battery thresholds are configured operational
        rules unless backend evidence explicitly marks them official.
      </p>
      <ToolEvidencePanel
        tool={active[1]}
        label={active[0]}
        parameters={{ latest_available: true }}
      />
    </>
  );
}
