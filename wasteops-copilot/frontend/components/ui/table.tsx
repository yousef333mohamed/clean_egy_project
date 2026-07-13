import type {
  HTMLAttributes,
  TableHTMLAttributes,
  ThHTMLAttributes,
  TdHTMLAttributes,
} from "react";
import { cn } from "@/lib/utils";
export const Table = ({
  className,
  ...props
}: TableHTMLAttributes<HTMLTableElement>) => (
  <div className="w-full overflow-auto">
    <table className={cn("w-full text-sm", className)} {...props} />
  </div>
);
export const TableHeader = (props: HTMLAttributes<HTMLTableSectionElement>) => (
  <thead className="border-b" {...props} />
);
export const TableBody = (props: HTMLAttributes<HTMLTableSectionElement>) => (
  <tbody {...props} />
);
export const TableRow = ({
  className,
  ...props
}: HTMLAttributes<HTMLTableRowElement>) => (
  <tr
    className={cn("hover:bg-muted/50 border-b transition-colors", className)}
    {...props}
  />
);
export const TableHead = ({
  className,
  ...props
}: ThHTMLAttributes<HTMLTableCellElement>) => (
  <th
    className={cn(
      "text-muted-foreground h-10 px-3 text-start align-middle font-medium",
      className,
    )}
    {...props}
  />
);
export const TableCell = ({
  className,
  ...props
}: TdHTMLAttributes<HTMLTableCellElement>) => (
  <td className={cn("p-3 align-middle", className)} {...props} />
);
