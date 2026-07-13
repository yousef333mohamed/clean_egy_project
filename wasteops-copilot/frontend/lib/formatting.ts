export function formatValue(value: unknown, unit?: string): string {
  if (value === null || value === undefined) return "Not available";
  const text =
    typeof value === "number"
      ? new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(
          value,
        )
      : String(value);
  return unit ? `${text} ${unit}` : text;
}
export function formatDate(value: string | null | undefined): string {
  if (!value) return "Date unavailable";
  const date = new Date(value);
  return Number.isNaN(date.valueOf())
    ? value
    : new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: value.includes("T") ? "short" : undefined,
      }).format(date);
}
export function formatDuration(value: number | null): string {
  return value === null
    ? "Unavailable"
    : value < 1000
      ? `${Math.round(value)} ms`
      : `${(value / 1000).toFixed(2)} s`;
}
