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
  Settings2,
  Sparkles,
  Truck,
  Users,
} from "lucide-react";
import { env } from "@/lib/env";
import { cn } from "@/lib/utils";

const primary = [
  ["Overview", "/", LayoutDashboard],
  ["AI Assistant", "/assistant", Bot],
  ["Analytics", "/analytics", Gauge],
  ["Decisions", "/decisions", ClipboardCheck],
  ["Bins", "/bins", Boxes],
  ["Trucks", "/trucks", Truck],
  ["Workforce", "/workforce", Users],
  ["Documents", "/documents", FileText],
] as const;
const system = [
  ["Evaluations", "/system/evaluations", Activity],
  ["Traces", "/system/traces", History],
  ["Prompt Versions", "/system/prompts", MessageSquareText],
] as const;
export function AppSidebar({
  onNavigate,
  className,
}: {
  onNavigate?: () => void;
  className?: string;
}) {
  const pathname = usePathname();
  const items = env.NEXT_PUBLIC_ENABLE_INGESTION_PAGES
    ? [...primary, ["Ingestion", "/ingestion", Import] as const]
    : primary;
  const systemItems = system.filter(
    ([name]) =>
      env.NEXT_PUBLIC_ENABLE_ADMIN_PAGES &&
      (name !== "Evaluations" || env.NEXT_PUBLIC_ENABLE_EVALUATION_PAGES) &&
      (name !== "Prompt Versions" || env.NEXT_PUBLIC_ENABLE_PROMPT_PAGES),
  );
  const nav = (
    entries: readonly (readonly [string, string, React.ElementType])[],
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
        Authentication and RBAC pending
      </div>
    </aside>
  );
}
