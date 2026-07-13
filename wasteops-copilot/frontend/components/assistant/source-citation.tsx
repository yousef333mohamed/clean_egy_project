"use client";
import type { Citation, OperationalEvidence } from "@/lib/schemas/api";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
export function SourceCitation({
  id,
  document,
  database,
}: {
  id: string;
  document?: Citation;
  database?: OperationalEvidence;
}) {
  const kind =
    id[0] === "S"
      ? "Document"
      : id[0] === "D"
        ? "Database"
        : id[0] === "R"
          ? "Rule"
          : "Model";
  const disabled = !document && !database;
  const chip = (
    <Badge
      className={
        id[0] === "S"
          ? "border-blue-300 bg-blue-50 text-blue-800 dark:bg-blue-950 dark:text-blue-200"
          : id[0] === "D"
            ? "border-emerald-300 bg-emerald-50 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200"
            : "border-amber-300 bg-amber-50 text-amber-800 dark:bg-amber-950 dark:text-amber-200"
      }
    >
      {id} · {kind}
    </Badge>
  );
  if (disabled) return chip;
  return (
    <Dialog>
      <DialogTrigger
        className="rounded focus-visible:ring-2"
        aria-label={`Open ${id} evidence`}
      >
        {chip}
      </DialogTrigger>
      <DialogContent
        title={`${id} ${kind} evidence`}
        description="Backend-supplied evidence summary. SQL, embeddings, and full documents are never displayed."
      >
        {document && (
          <dl className="grid gap-3 text-sm sm:grid-cols-2">
            <Detail label="Title" value={document.document_title} />
            <Detail label="Filename" value={document.source_filename} />
            <Detail label="Section" value={document.section_title} />
            <Detail label="Page" value={document.page_number} />
            <Detail
              label="Synthetic status"
              value={
                document.is_synthetic
                  ? "Synthetic demo"
                  : "Not marked synthetic"
              }
            />
            <div className="sm:col-span-2">
              <dt className="text-muted-foreground">Content preview</dt>
              <dd className="bg-muted mt-1 rounded-lg p-3">
                {document.content_preview}
              </dd>
            </div>
          </dl>
        )}
        {database && (
          <div className="space-y-4">
            <dl className="grid gap-3 text-sm sm:grid-cols-2">
              <Detail label="Analytics tool" value={database.tool_name} />
              <Detail label="Metric" value={database.metric} />
              <Detail
                label="Date range"
                value={`${database.data_period.start ?? "unknown"} – ${database.data_period.end ?? "unknown"}`}
              />
              <Detail label="Record count" value={database.record_count} />
            </dl>
            <Table>
              <TableHeader>
                <TableRow>
                  {database.columns.map((column) => (
                    <TableHead key={column}>{column}</TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {database.rows.slice(0, 20).map((row, index) => (
                  <TableRow key={index}>
                    {database.columns.map((column) => (
                      <TableCell key={column}>
                        {row[column] === null || row[column] === undefined
                          ? "Not available"
                          : String(row[column])}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
function Detail({ label, value }: { label: string; value: unknown }) {
  return (
    <div>
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="font-medium">
        {value === null || value === undefined
          ? "Not available"
          : String(value)}
      </dd>
    </div>
  );
}
