"use client";
import { Square, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
export function ChatInput({
  value,
  onChange,
  onSubmit,
  onCancel,
  pending,
}: {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onCancel: () => void;
  pending: boolean;
}) {
  return (
    <div className="bg-background sticky bottom-0 space-y-2 border-t py-4">
      <label htmlFor="assistant-question" className="sr-only">
        Ask WasteOps
      </label>
      <div className="flex items-end gap-2">
        <Textarea
          id="assistant-question"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Ask about documented guidance, operational data, or a decision…"
          maxLength={4000}
          disabled={pending}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSubmit();
            }
          }}
        />
        <Button
          size="icon"
          aria-label={pending ? "Cancel request" : "Submit question"}
          onClick={pending ? onCancel : onSubmit}
          disabled={!pending && !value.trim()}
        >
          {pending ? (
            <Square className="size-4" />
          ) : (
            <Send className="size-4" />
          )}
        </Button>
      </div>
      <p className="text-muted-foreground text-xs">
        Enter to submit · Shift+Enter for a new line · Generated responses
        cannot execute operational actions.
      </p>
    </div>
  );
}
