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
  return (
    <div
      className="h-72 w-full"
      role="img"
      aria-label={`Bar chart of ${metric} by ${dimension}`}
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={dimension} />
          <YAxis />
          <Tooltip />
          <Bar dataKey={metric} fill="var(--primary)" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
