"use client";
import { useQuery } from "@tanstack/react-query";
import { useTheme } from "next-themes";
import { CircleUserRound, Database, Moon, Server, Sun } from "lucide-react";
import { getDatabaseHealth, getHealth } from "@/lib/api/health";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Breadcrumbs } from "./breadcrumbs";
import { MobileNavigation } from "./mobile-navigation";
export function AppHeader() {
  const backend = useQuery({
    queryKey: ["health"],
    queryFn: ({ signal }) => getHealth(signal),
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
  const database = useQuery({
    queryKey: ["database-health"],
    queryFn: ({ signal }) => getDatabaseHealth(signal),
    enabled: backend.isSuccess,
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
  const { resolvedTheme, setTheme } = useTheme();
  const state = backend.isPending
    ? "Checking"
    : backend.isError
      ? "Backend unavailable"
      : database.isError
        ? "Database unavailable"
        : database.isSuccess
          ? "Connected"
          : "Checking";
  return (
    <header className="bg-background/95 sticky top-0 z-30 flex h-16 items-center justify-between border-b px-4 backdrop-blur md:px-6">
      <div className="flex items-center gap-3">
        <MobileNavigation />
        <Breadcrumbs />
      </div>
      <div className="flex items-center gap-2">
        <Badge aria-live="polite" className="gap-1.5">
          <span
            className={
              state === "Connected"
                ? "text-emerald-600"
                : state === "Checking"
                  ? "text-amber-600"
                  : "text-destructive"
            }
          >
            {state === "Database unavailable" ? (
              <Database className="size-3" />
            ) : (
              <Server className="size-3" />
            )}
          </span>
          <span>{state}</span>
        </Badge>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Toggle color theme"
          onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
        >
          {resolvedTheme === "dark" ? (
            <Sun className="size-4" />
          ) : (
            <Moon className="size-4" />
          )}
        </Button>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Future user menu"
          title="Authentication will be added later"
        >
          <CircleUserRound className="size-5" />
        </Button>
      </div>
    </header>
  );
}
