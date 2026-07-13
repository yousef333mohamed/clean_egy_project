import { AlertTriangle, DatabaseZap, Info } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
export function StatePanel({
  title,
  description,
  kind = "empty",
}: {
  title: string;
  description: string;
  kind?: "error" | "empty" | "warning";
}) {
  const Icon =
    kind === "error" ? DatabaseZap : kind === "warning" ? AlertTriangle : Info;
  return (
    <Card role={kind === "error" ? "alert" : "status"}>
      <CardContent className="flex items-start gap-3 p-5">
        <Icon
          className={
            kind === "error"
              ? "text-destructive mt-0.5 size-5"
              : "mt-0.5 size-5 text-amber-600"
          }
        />
        <div>
          <p className="font-medium">{title}</p>
          <p className="text-muted-foreground mt-1 text-sm">{description}</p>
        </div>
      </CardContent>
    </Card>
  );
}
