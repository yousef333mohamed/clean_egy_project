"use client";
import {
  AlertCircle,
  BatteryLow,
  Boxes,
  CircleGauge,
  ClipboardX,
  MessageSquareWarning,
  Siren,
  Truck,
  Users,
} from "lucide-react";
import { useOperationalOverview } from "@/hooks/use-operational-overview";
import { MetricCard } from "./metric-card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatePanel } from "@/components/shared/state-panel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
export function OperationalOverview() {
  const query = useOperationalOverview();
  if (query.isPending)
    return (
      <div
        className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3"
        aria-label="Loading operational metrics"
      >
        {Array.from({ length: 9 }, (_, i) => (
          <Skeleton key={i} className="h-36" />
        ))}
      </div>
    );
  if (query.isError)
    return (
      <StatePanel
        kind="error"
        title="Operational overview unavailable"
        description="Confirm the backend and database are running, then retry. No placeholder values are shown."
      />
    );
  const row = query.data.rows[0];
  if (!row)
    return (
      <StatePanel
        title="No operational data"
        description="Ingest operational datasets to populate this dashboard."
      />
    );
  const configured =
    "Configured thresholds are operational rules, not official policy.";
  const metrics = [
    [
      "Total smart bins",
      row.total_bins,
      undefined,
      row.bin_status_effective_timestamp,
      undefined,
      Boxes,
    ],
    [
      "Latest critical bins",
      row.latest_critical_bins,
      undefined,
      row.bin_status_effective_timestamp,
      configured,
      AlertCircle,
    ],
    [
      "Latest low-battery bins",
      row.latest_low_battery_bins,
      undefined,
      row.bin_status_effective_timestamp,
      configured,
      BatteryLow,
    ],
    [
      "Latest sensor-fault bins",
      row.latest_sensor_fault_bins,
      undefined,
      row.bin_status_effective_timestamp,
      undefined,
      CircleGauge,
    ],
    [
      "Missed collections",
      row.missed_collection_count,
      undefined,
      row.operations_effective_date,
      undefined,
      ClipboardX,
    ],
    [
      "Emergency requests",
      row.emergency_request_count,
      undefined,
      row.operations_effective_date,
      undefined,
      Siren,
    ],
    [
      "Complaints",
      row.complaint_count,
      undefined,
      row.operations_effective_date,
      undefined,
      MessageSquareWarning,
    ],
    [
      "Trip count",
      row.trip_count,
      undefined,
      row.trucks_effective_date,
      undefined,
      Truck,
    ],
    [
      "Attendance rate",
      row.attendance_rate_pct,
      "%",
      row.workforce_effective_date,
      undefined,
      Users,
    ],
  ] as const;
  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {metrics.map(([label, value, unit, period, warning, icon]) => (
          <MetricCard
            key={label}
            label={label}
            value={value}
            unit={unit}
            period={period ? String(period) : null}
            warning={warning}
            icon={icon}
          />
        ))}
      </div>
      {query.data.notes.length > 0 && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="size-4 text-amber-600" />
              Latest system warnings
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="text-muted-foreground space-y-2 text-sm">
              {query.data.notes.map((note) => (
                <li key={note}>• {note}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </>
  );
}
