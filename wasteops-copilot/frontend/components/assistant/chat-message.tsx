"use client";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Citation, OperationalEvidence } from "@/lib/schemas/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SourceCitation } from "./source-citation";
import { AnswerWarning } from "./answer-warning";
import { parseCitations } from "@/lib/citations";
import { FeedbackForm } from "@/components/feedback/feedback-form";
export interface ChatMessageModel {
  id: string;
  role: "user" | "assistant";
  content: string;
  mode: string;
  requestId?: string;
  warnings?: string[];
  insufficient?: boolean;
  missing?: string[];
  requiresApproval?: boolean;
  citations?: Citation[];
  databaseEvidence?: OperationalEvidence[];
}
export function ChatMessage({ message }: { message: ChatMessageModel }) {
  const references = parseCitations(message.content);
  return (
    <article
      aria-label={`${message.role} message`}
      className={message.role === "user" ? "ms-auto max-w-2xl" : "max-w-4xl"}
    >
      <Card className={message.role === "user" ? "bg-secondary" : ""}>
        <CardContent className="space-y-4 p-4">
          <div className="flex items-center justify-between gap-3">
            <Badge>{message.role === "user" ? "You" : message.mode}</Badge>
            {message.requestId && (
              <code className="text-muted-foreground text-xs">
                Request {message.requestId}
              </code>
            )}
          </div>
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml>
              {message.content}
            </ReactMarkdown>
          </div>
          {references.length > 0 && (
            <div className="flex flex-wrap gap-2" aria-label="Sources">
              {[...new Set(references.map((item) => item.id))].map((id) => (
                <SourceCitation
                  key={id}
                  id={id}
                  document={message.citations?.find(
                    (item) => item.citation_id === id,
                  )}
                  database={message.databaseEvidence?.find(
                    (item) => item.evidence_id === id,
                  )}
                />
              ))}
            </div>
          )}
          {message.insufficient && (
            <AnswerWarning>
              Insufficient context: the backend could not find enough grounded
              evidence. Refine the question or filters.
            </AnswerWarning>
          )}
          {message.warnings?.map((warning) => (
            <AnswerWarning key={warning}>{warning}</AnswerWarning>
          ))}
          {message.missing && message.missing.length > 0 && (
            <div>
              <p className="text-sm font-medium">Missing information</p>
              <ul className="text-muted-foreground mt-1 list-inside list-disc text-sm">
                {message.missing.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}
          {message.requiresApproval && (
            <AnswerWarning>
              This recommendation is decision support only. An authorized
              operations manager must review it before execution.
            </AnswerWarning>
          )}
          {message.role === "assistant" && message.requestId && (
            <FeedbackForm requestId={message.requestId} />
          )}
        </CardContent>
      </Card>
    </article>
  );
}
