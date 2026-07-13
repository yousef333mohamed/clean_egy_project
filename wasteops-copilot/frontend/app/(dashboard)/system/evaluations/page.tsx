import { PageHeader } from "@/components/layout/page-header";
import { EvaluationWorkspace } from "@/components/evaluations/evaluation-workspace";
import { env } from "@/lib/env";
import { StatePanel } from "@/components/shared/state-panel";
export default function EvaluationsPage() {
  return (
    <>
      <PageHeader
        title="Evaluation quality gates"
        description="Run repeatable deterministic suites without external model providers."
      />
      {env.NEXT_PUBLIC_ENABLE_EVALUATION_PAGES ? (
        <EvaluationWorkspace />
      ) : (
        <StatePanel
          kind="warning"
          title="Evaluation pages disabled"
          description="Enable the frontend flag and ensure the backend administrative API is protected before production."
        />
      )}
    </>
  );
}
