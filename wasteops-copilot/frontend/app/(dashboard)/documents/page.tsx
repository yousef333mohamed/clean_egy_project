"use client";
import { PageHeader } from "@/components/layout/page-header";
import { useDocuments } from "@/hooks/use-documents";
import { Skeleton } from "@/components/ui/skeleton";
import { StatePanel } from "@/components/shared/state-panel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DocumentStatusBadge } from "@/components/documents/document-status-badge";
import { formatDate } from "@/lib/formatting";
export default function DocumentsPage() {
  const query = useDocuments();
  return (
    <>
      <PageHeader
        title="Knowledge documents"
        description="Versioned knowledge sources and authority metadata. Vector values and complete document content are never shown."
      />
      {query.isPending ? (
        <Skeleton className="h-72" />
      ) : query.isError ? (
        <StatePanel
          kind="error"
          title="Documents unavailable"
          description="Check document API availability and retry."
        />
      ) : query.data.items.length === 0 ? (
        <StatePanel
          title="No documents"
          description="Discover and ingest supported knowledge documents from the ingestion page."
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {query.data.items.map((document) => (
            <Card key={document.document_id}>
              <CardHeader>
                <CardTitle>{document.title}</CardTitle>
                <p className="text-muted-foreground text-sm" data-identifier>
                  {document.source_filename}
                </p>
                <DocumentStatusBadge
                  synthetic={document.is_synthetic}
                  authority={document.authority_level}
                  active={document.is_active}
                  status={document.status}
                />
              </CardHeader>
              <CardContent>
                <dl className="grid grid-cols-2 gap-3 text-sm">
                  <Detail label="Type" value={document.document_type} />
                  <Detail label="Department" value={document.department} />
                  <Detail label="Region" value={document.region} />
                  <Detail label="Language" value={document.language} />
                  <Detail label="Version" value={document.version} />
                  <Detail
                    label="Effective"
                    value={formatDate(document.effective_date)}
                  />
                  <Detail label="Chunks" value={document.total_chunks} />
                  <Detail
                    label="Updated"
                    value={formatDate(document.updated_at)}
                  />
                </dl>
                <details className="mt-4 rounded-lg border p-3">
                  <summary className="cursor-pointer text-sm font-medium">
                    Metadata
                  </summary>
                  <pre className="text-muted-foreground mt-2 overflow-auto text-xs">
                    {JSON.stringify(document.metadata_json, null, 2)}
                  </pre>
                </details>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </>
  );
}
function Detail({ label, value }: { label: string; value: unknown }) {
  return (
    <div>
      <dt className="text-muted-foreground">{label}</dt>
      <dd>
        {value === null || value === undefined
          ? "Not available"
          : String(value)}
      </dd>
    </div>
  );
}
