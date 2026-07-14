"use client";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
export function AnalyticsChart({
  columns,
  rows,
}: {
  columns: string[];
  rows: Record<string, unknown>[];
}) {
  const dimension = columns.find((column) =>
    rows.every((row) => typeof row[column] === "string"),
  );
  const metric = columns.find((column) =>
    rows.every((row) => typeof row[column] === "number"),
  );
  if (
    !dimension ||
    !metric ||
    rows.length < 2 ||
    rows.some((row) => row[metric] === null)
  )
    return null;
  const angleAssetLabels = dimension === "bin_id" || dimension === "truck_id";
  const minimumChartWidth = angleAssetLabels
    ? Math.max(720, rows.length * 64)
    : undefined;
  return (
    <div
      className={angleAssetLabels ? "h-80 w-full overflow-x-auto" : "h-72 w-full"}
      role="img"
      aria-label={`Bar chart of ${metric} by ${dimension}`}
    >
      <div className="h-full w-full" style={{ minWidth: minimumChartWidth }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey={dimension}
              angle={angleAssetLabels ? -45 : 0}
              textAnchor={angleAssetLabels ? "end" : "middle"}
              height={angleAssetLabels ? 72 : 30}
              interval={angleAssetLabels ? 0 : "preserveEnd"}
            />
            <YAxis />
            <Tooltip />
            <Bar dataKey={metric} fill="var(--primary)" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
