import { PageHeader } from "@/components/layout/page-header";
import { PromptWorkspace } from "@/components/prompts/prompt-workspace";
import { env } from "@/lib/env";
import { StatePanel } from "@/components/shared/state-panel";
export default function PromptsPage() {
  return (
    <>
      <PageHeader
        title="Prompt versions"
        description="Immutable prompt metadata and controlled activation. Authentication and RBAC are required before production."
      />
      {env.NEXT_PUBLIC_ENABLE_PROMPT_PAGES ? (
        <PromptWorkspace />
      ) : (
        <StatePanel
          kind="warning"
          title="Prompt pages disabled"
          description="Frontend feature flags are presentation controls, not authorization."
        />
      )}
    </>
  );
}
