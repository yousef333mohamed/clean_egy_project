"use client";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { useDocumentFiles, useIngestionFiles } from "@/hooks/use-ingestion";
import { ingestDataset, validateDataset } from "@/lib/api/ingestion";
import { ingestDocument, validateDocument } from "@/lib/api/documents";
import { userErrorMessage } from "@/lib/api/errors";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ConfirmationAction } from "./confirmation-action";
import { Skeleton } from "@/components/ui/skeleton";
import { StatePanel } from "@/components/shared/state-panel";
export function IngestionWorkspace() {
  const files = useIngestionFiles();
  const documents = useDocumentFiles();
  const client = useQueryClient();
  const mutation = useMutation({
    mutationFn: ({
      kind,
      id,
      action,
    }: {
      kind: "data" | "document";
      id: string;
      action: "validate" | "ingest";
    }) =>
      kind === "data"
        ? action === "validate"
          ? validateDataset(id)
          : ingestDataset(id)
        : action === "validate"
          ? validateDocument(id)
          : ingestDocument(id),
    onSuccess: () => {
      toast.success("Backend processing completed");
      void client.invalidateQueries();
    },
    onError: (e) => toast.error(userErrorMessage(e)),
  });
  return (
    <div className="space-y-8">
      <section>
        <h2 className="mb-3 text-lg font-semibold">Structured data</h2>
        {files.isPending ? (
          <Skeleton className="h-40" />
        ) : files.isError ? (
          <StatePanel
            kind="error"
            title="Dataset discovery unavailable"
            description="Check the ingestion API."
          />
        ) : (
          <div className="grid gap-3 md:grid-cols-2">
            {files.data.map((file) => (
              <Card key={file.dataset}>
                <CardHeader>
                  <CardTitle>{file.dataset}</CardTitle>
                  <Badge>{file.available ? "Available" : "Unavailable"}</Badge>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground mb-4 text-sm">
                    {file.filename ?? "No discovered file"} ·{" "}
                    {file.size_bytes ?? "size unavailable"} bytes
                  </p>
                  <div className="flex gap-2">
                    <ConfirmationAction
                      label="Validate"
                      title={`Validate ${file.dataset}`}
                      description="Validation does not insert records."
                      pending={mutation.isPending}
                      onConfirm={() =>
                        mutation.mutate({
                          kind: "data",
                          id: file.dataset,
                          action: "validate",
                        })
                      }
                    />
                    <ConfirmationAction
                      label="Ingest"
                      title={`Ingest ${file.dataset}`}
                      description="This writes validated records and creates an audited ingestion run."
                      pending={mutation.isPending}
                      onConfirm={() =>
                        mutation.mutate({
                          kind: "data",
                          id: file.dataset,
                          action: "ingest",
                        })
                      }
                    />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>
      <section>
        <h2 className="mb-1 text-lg font-semibold">Knowledge documents</h2>
        <p className="text-muted-foreground mb-3 text-sm">
          Validation extracts and chunks content but does not create embeddings.
        </p>
        {documents.isPending ? (
          <Skeleton className="h-40" />
        ) : documents.isError ? (
          <StatePanel
            kind="error"
            title="Document discovery unavailable"
            description="Check the document API."
          />
        ) : (
          <div className="grid gap-3 md:grid-cols-2">
            {documents.data.map((file) => (
              <Card key={file.relative_path}>
                <CardHeader>
                  <CardTitle>{file.filename}</CardTitle>
                  <Badge>{file.supported ? "Supported" : "Unsupported"}</Badge>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground mb-4 text-sm">
                    {file.relative_path} · {file.size_bytes} bytes
                  </p>
                  <div className="flex gap-2">
                    <ConfirmationAction
                      label="Validate"
                      title={`Validate ${file.filename}`}
                      description="No embeddings will be created."
                      pending={mutation.isPending}
                      onConfirm={() =>
                        mutation.mutate({
                          kind: "document",
                          id: file.relative_path,
                          action: "validate",
                        })
                      }
                    />
                    <ConfirmationAction
                      label="Ingest"
                      title={`Ingest ${file.filename}`}
                      description="This creates versioned chunks and embeddings through the backend."
                      pending={mutation.isPending}
                      onConfirm={() =>
                        mutation.mutate({
                          kind: "document",
                          id: file.relative_path,
                          action: "ingest",
                        })
                      }
                    />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
