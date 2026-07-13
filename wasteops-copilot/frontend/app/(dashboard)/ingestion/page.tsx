import { PageHeader } from "@/components/layout/page-header";
import { IngestionWorkspace } from "@/components/ingestion/ingestion-workspace";
export default function IngestionPage() {
  return (
    <>
      <PageHeader
        title="Data ingestion"
        description="Validate and ingest only allow-listed backend-discovered datasets and documents."
      />
      <IngestionWorkspace />
    </>
  );
}
