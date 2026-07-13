import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
const actions = [
  ["Review critical bins", "/bins?tab=critical"],
  ["Review sensor faults", "/bins?tab=sensors"],
  ["Review low-battery bins", "/bins?tab=battery"],
  ["Investigate missed collections", "/analytics?q=missed+collections"],
  ["Ask the AI assistant", "/assistant"],
  ["Generate a decision recommendation", "/decisions"],
];
export function QuickActions() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Priority actions</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-2 sm:grid-cols-2">
        {actions.map(([label, href]) => (
          <Link
            key={label}
            href={href}
            className="hover:bg-muted flex items-center justify-between rounded-lg border p-3 text-sm font-medium"
          >
            {label}
            <ArrowUpRight className="size-4" />
          </Link>
        ))}
      </CardContent>
    </Card>
  );
}
