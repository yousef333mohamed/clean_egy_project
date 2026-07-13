import { ModelManagement } from "@/components/models/model-management";
import { PageHeader } from "@/components/layout/page-header";

export default function ModelsPage() {
  return <><PageHeader title="Model management" description="Protected production-model metadata, health, drift signals, and promotion review requests." /><ModelManagement /></>;
}
