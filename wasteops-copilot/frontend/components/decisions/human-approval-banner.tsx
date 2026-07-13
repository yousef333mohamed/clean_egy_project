import { ShieldCheck } from "lucide-react";
export function HumanApprovalBanner() {
  return (
    <div
      role="alert"
      className="flex items-start gap-3 rounded-xl border-2 border-amber-400 bg-amber-50 p-4 text-amber-950 dark:bg-amber-950/40 dark:text-amber-100"
    >
      <ShieldCheck className="mt-0.5 size-5 shrink-0" />
      <div>
        <p className="font-semibold">Human approval required</p>
        <p className="text-sm">
          This recommendation is decision support only. An authorized operations
          manager must review it before execution.
        </p>
      </div>
    </div>
  );
}
