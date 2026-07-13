"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight } from "lucide-react";
export function Breadcrumbs() {
  const parts = usePathname().split("/").filter(Boolean);
  return (
    <nav
      aria-label="Breadcrumb"
      className="text-muted-foreground hidden items-center gap-1 text-xs sm:flex"
    >
      <Link href="/">Overview</Link>
      {parts.map((part, index) => (
        <span key={part} className="flex items-center gap-1">
          <ChevronRight className="size-3 rtl:rotate-180" />
          <span
            className="capitalize"
            aria-current={index === parts.length - 1 ? "page" : undefined}
          >
            {part.replaceAll("-", " ")}
          </span>
        </span>
      ))}
    </nav>
  );
}
