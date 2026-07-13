import { Badge } from "@/components/ui/badge";
export function DocumentStatusBadge({
  synthetic,
  authority,
  active,
  status,
}: {
  synthetic: boolean | null;
  authority: string;
  active: boolean;
  status: string;
}) {
  return (
    <div className="flex flex-wrap gap-1">
      {synthetic ? (
        <Badge className="border-amber-400 bg-amber-50 text-amber-900 dark:bg-amber-950 dark:text-amber-100">
          Synthetic demo
        </Badge>
      ) : authority === "official" ? (
        <Badge className="border-emerald-400 bg-emerald-50 text-emerald-900 dark:bg-emerald-950 dark:text-emerald-100">
          Official
        </Badge>
      ) : (
        <Badge>Unknown authority</Badge>
      )}
      <Badge>{active ? "Active" : "Replaced or inactive"}</Badge>
      <Badge>{status}</Badge>
    </div>
  );
}
