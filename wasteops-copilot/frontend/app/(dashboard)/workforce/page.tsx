import { PageHeader } from "@/components/layout/page-header";
import { ToolEvidencePanel } from "@/components/shared/tool-evidence-panel";
import { StatePanel } from "@/components/shared/state-panel";
export default function WorkforcePage() {
  return (
    <>
      <PageHeader
        title="Workforce summary"
        description="Attendance and task summaries for management visibility. Performance data is not a disciplinary recommendation."
      />
      <div className="space-y-5">
        <StatePanel
          title="Responsible use"
          description="Use these summaries to understand coverage and data completeness, not to automate assignments or disciplinary action."
        />
        <ToolEvidencePanel
          tool="get_workforce_summary"
          label="Workforce summary"
          parameters={{ latest_available: true }}
        />
      </div>
    </>
  );
}
