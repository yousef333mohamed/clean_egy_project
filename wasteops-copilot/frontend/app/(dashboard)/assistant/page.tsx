import { ChatContainer } from "@/components/assistant/chat-container";
import { PageHeader } from "@/components/layout/page-header";
export default function AssistantPage() {
  return (
    <>
      <PageHeader
        title="AI Assistant"
        description="Choose a visible evidence mode. Answers remain grounded in backend documents, operational data, or deterministic decision support."
      />
      <ChatContainer />
    </>
  );
}
