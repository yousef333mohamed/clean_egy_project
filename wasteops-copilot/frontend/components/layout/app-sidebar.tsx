"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Bot,
  Boxes,
  ClipboardCheck,
  FileText,
  Gauge,
  History,
  Import,
  LayoutDashboard,
  MessageSquareText,
  BrainCircuit,
  Settings2,
  Sparkles,
  Truck,
  Users,
} from "lucide-react";
import { env } from "@/lib/env";
import { cn } from "@/lib/utils";

const primary = [
  ["Overview", "/", LayoutDashboard, "dashboard:read"],
  ["AI Assistant", "/assistant", Bot, "assistant:use"],
  ["Analytics", "/analytics", Gauge, "analytics:read"],
  ["Decisions", "/decisions", ClipboardCheck, "decisions:request"],
  ["Bins", "/bins", Boxes, "analytics:read"],
  ["Trucks", "/trucks", Truck, "analytics:read"],
  ["Workforce", "/workforce", Users, "analytics:read"],
  ["Documents", "/documents", FileText, "documents:read"],
] as const;
const system = [
  ["Models", "/system/models", BrainCircuit, "system:configure"],
  ["Evaluations", "/system/evaluations", Activity, "evaluations:read"],
  ["Traces", "/system/traces", History, "traces:read"],
  ["Prompt Versions", "/system/prompts", MessageSquareText, "prompts:read"],
] as const;
export function AppSidebar({
  onNavigate,
  className,
  permissions,
}: {
  onNavigate?: () => void;
  className?: string;
  permissions?: string[];
}) {
  const pathname = usePathname();
  const visible = (permission: string) => !permissions || permissions.includes(permission);
  const items = (env.NEXT_PUBLIC_ENABLE_INGESTION_PAGES
    ? [...primary, ["Ingestion", "/ingestion", Import, "datasets:read"] as const]
    : [...primary]).filter((entry) => visible(entry[3]));
  const systemItems = system.filter(
    ([name, , , permission]) =>
      env.NEXT_PUBLIC_ENABLE_ADMIN_PAGES &&
      visible(permission) &&
      (name !== "Evaluations" || env.NEXT_PUBLIC_ENABLE_EVALUATION_PAGES) &&
      (name !== "Prompt Versions" || env.NEXT_PUBLIC_ENABLE_PROMPT_PAGES),
  );
  const nav = (
    entries: readonly (readonly [string, string, React.ElementType, string])[],
  ) =>
    entries.map(([label, href, Icon]) => {
      const active =
        href === "/" ? pathname === href : pathname.startsWith(href);
      return (
        <Link
          key={href}
          href={href}
          onClick={onNavigate}
          aria-current={active ? "page" : undefined}
          className={cn(
            "text-muted-foreground hover:bg-muted hover:text-foreground flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium",
            active && "bg-secondary text-secondary-foreground",
          )}
        >
          <Icon className="size-4" aria-hidden="true" />
          {label}
        </Link>
      );
    });
  return (
    <aside
      className={cn("bg-card flex h-full w-64 flex-col border-e", className)}
    >
      <div className="flex h-16 items-center gap-3 border-b px-5">
        <div className="bg-primary text-primary-foreground grid size-9 place-items-center rounded-lg">
          <Sparkles className="size-5" />
        </div>
        <div>
          <p className="font-semibold">WasteOps</p>
          <p className="text-muted-foreground text-xs">
            Decision command center
          </p>
        </div>
      </div>
      <nav
        aria-label="Main navigation"
        className="flex-1 space-y-1 overflow-y-auto p-3"
      >
        {nav(items)}
        {systemItems.length > 0 && (
          <>
            <p className="text-muted-foreground px-3 pt-5 pb-1 text-xs font-semibold tracking-wider uppercase">
              System
            </p>
            {nav(systemItems)}
          </>
        )}
      </nav>
      <div className="text-muted-foreground border-t p-4 text-xs">
        <Settings2 className="me-2 inline size-3" />
        Backend-enforced identity and access
      </div>
    </aside>
  );
}
