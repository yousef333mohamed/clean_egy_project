"use client";
import { useRef, useState } from "react";
import { toast } from "sonner";
import { askRag, askHybrid } from "@/lib/api/chat";
import { queryAnalytics } from "@/lib/api/analytics";
import { recommendDecision } from "@/lib/api/decisions";
import { userErrorMessage } from "@/lib/api/errors";
import { Button } from "@/components/ui/button";
import { ChatInput } from "./chat-input";
import { ChatMessage, type ChatMessageModel } from "./chat-message";
import { SuggestedQuestions } from "./suggested-questions";
type Mode = "Knowledge" | "Operational Data" | "Hybrid" | "Decision Support";
export function ChatContainer() {
  const [mode, setMode] = useState<Mode>("Knowledge");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessageModel[]>([]);
  const [pending, setPending] = useState(false);
  const controller = useRef<AbortController | null>(null);
  async function submit() {
    const text = question.trim();
    if (!text || pending) return;
    setMessages((items) => [
      ...items,
      { id: crypto.randomUUID(), role: "user", content: text, mode },
    ]);
    setQuestion("");
    setPending(true);
    controller.current = new AbortController();
    try {
      let response: ChatMessageModel;
      if (mode === "Knowledge") {
        const data = await askRag(text, controller.current.signal);
        response = {
          id: crypto.randomUUID(),
          role: "assistant",
          mode,
          content: data.answer,
          requestId: data.request_id,
          warnings: data.warnings,
          insufficient: data.insufficient_context,
          citations: data.citations,
        };
      } else if (mode === "Operational Data") {
        const data = await queryAnalytics(text, controller.current.signal);
        response = {
          id: crypto.randomUUID(),
          role: "assistant",
          mode,
          content: data.answer,
          requestId: data.request_id,
          warnings: data.warnings,
          insufficient: data.insufficient_data,
          databaseEvidence: data.database_evidence,
        };
      } else if (mode === "Hybrid") {
        const data = await askHybrid(text, controller.current.signal);
        response = {
          id: crypto.randomUUID(),
          role: "assistant",
          mode,
          content: data.answer,
          requestId: data.request_id,
          warnings: data.warnings,
          insufficient: data.insufficient_context || data.insufficient_data,
          citations: data.document_citations,
          databaseEvidence: data.database_evidence,
        };
      } else {
        const data = await recommendDecision(
          { question: text },
          controller.current.signal,
        );
        response = {
          id: crypto.randomUUID(),
          role: "assistant",
          mode,
          content: data.situation_summary,
          requestId: data.request_id,
          warnings: data.warnings,
          insufficient: data.insufficient_context,
          citations: data.document_citations,
          databaseEvidence: data.database_evidence,
          missing: data.missing_information,
          requiresApproval: true,
        };
      }
      setMessages((items) => [...items, response]);
    } catch (error) {
      if (!controller.current?.signal.aborted)
        toast.error(userErrorMessage(error));
    } finally {
      setPending(false);
      controller.current = null;
    }
  }
  return (
    <div className="space-y-5">
      <div
        role="radiogroup"
        aria-label="Assistant mode"
        className="flex flex-wrap gap-2"
      >
        {(
          [
            "Knowledge",
            "Operational Data",
            "Hybrid",
            "Decision Support",
          ] as Mode[]
        ).map((item) => (
          <Button
            key={item}
            variant={mode === item ? "default" : "outline"}
            role="radio"
            aria-checked={mode === item}
            onClick={() => setMode(item)}
          >
            {item}
          </Button>
        ))}
      </div>
      <p className="text-muted-foreground text-sm">
        Active mode: <strong className="text-foreground">{mode}</strong>. The
        mode remains fixed for each submitted question.
      </p>
      {messages.length === 0 ? (
        <SuggestedQuestions onSelect={setQuestion} />
      ) : (
        <div className="space-y-4" aria-live="polite">
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          {pending && (
            <p role="status" className="text-muted-foreground text-sm">
              Processing grounded evidence…
            </p>
          )}
        </div>
      )}
      <ChatInput
        value={question}
        onChange={setQuestion}
        onSubmit={submit}
        onCancel={() => controller.current?.abort()}
        pending={pending}
      />
      {messages.length > 0 && (
        <Button
          variant="ghost"
          onClick={() => setMessages([])}
          disabled={pending}
        >
          Clear conversation
        </Button>
      )}
    </div>
  );
}
