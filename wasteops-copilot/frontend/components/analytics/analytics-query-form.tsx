"use client";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { queryAnalytics } from "@/lib/api/analytics";
import { userErrorMessage } from "@/lib/api/errors";
import type { AnalyticsResponse } from "@/lib/schemas/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
export function AnalyticsQueryForm({
  onResult,
}: {
  onResult: (result: AnalyticsResponse) => void;
}) {
  const [question, setQuestion] = useState("");
  const mutation = useMutation({
    mutationFn: () => queryAnalytics(question),
    onSuccess: onResult,
    onError: (error) => toast.error(userErrorMessage(error)),
  });
  return (
    <form
      className="space-y-3"
      onSubmit={(e) => {
        e.preventDefault();
        if (question.trim() && !mutation.isPending) mutation.mutate();
      }}
    >
      <label className="block font-medium" htmlFor="analytics-question">
        Operational question
      </label>
      <Textarea
        id="analytics-question"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        maxLength={4000}
        placeholder="Which regions had the most missed collections last month?"
      />
      <div className="flex flex-wrap gap-2">
        <Button disabled={!question.trim() || mutation.isPending}>
          {mutation.isPending ? "Querying approved tools…" : "Run analytics"}
        </Button>
        {[
          "Show the latest operational overview",
          "Rank trucks by fuel use last month",
          "Show workforce attendance by region",
        ].map((item) => (
          <Button
            type="button"
            size="sm"
            variant="outline"
            key={item}
            onClick={() => setQuestion(item)}
          >
            {item}
          </Button>
        ))}
      </div>
    </form>
  );
}
