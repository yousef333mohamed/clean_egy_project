import type { LucideIcon } from "lucide-react";
import { AlertTriangle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { formatValue } from "@/lib/formatting";
export function MetricCard({
  label,
  value,
  unit,
  period,
  warning,
  icon: Icon,
}: {
  label: string;
  value: unknown;
  unit?: string;
  period?: string | null;
  warning?: string;
  icon: LucideIcon;
}) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-muted-foreground text-sm font-medium">{label}</p>
            <p className="mt-2 text-2xl font-semibold tabular-nums">
              {formatValue(value, unit)}
            </p>
          </div>
          <span className="bg-secondary text-secondary-foreground rounded-lg p-2">
            <Icon className="size-4" />
          </span>
        </div>
        <p className="text-muted-foreground mt-3 text-xs">
          {period || "Effective date unavailable"}
        </p>
        {warning && (
          <p className="mt-2 flex items-start gap-1 text-xs text-amber-700 dark:text-amber-400">
            <AlertTriangle className="mt-0.5 size-3 shrink-0" />
            {warning}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
