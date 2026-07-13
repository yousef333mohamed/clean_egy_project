"use client";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { submitFeedback } from "@/lib/api/feedback";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
const types = [
  "HELPFUL",
  "NOT_HELPFUL",
  "INCORRECT_DATA",
  "MISSING_SOURCE",
  "BAD_RECOMMENDATION",
  "UNSAFE",
  "OTHER",
];
export function FeedbackForm({ requestId }: { requestId: string }) {
  const [rating, setRating] = useState(0);
  const [type, setType] = useState("HELPFUL");
  const [comment, setComment] = useState("");
  const mutation = useMutation({
    mutationFn: () =>
      submitFeedback({
        request_id: requestId,
        rating,
        feedback_type: type,
        comment: comment.trim() || undefined,
      }),
    onSuccess: () => toast.success("Feedback recorded"),
    onError: () => toast.error("Feedback could not be submitted"),
  });
  return (
    <form
      className="space-y-3 border-t pt-4"
      onSubmit={(event) => {
        event.preventDefault();
        if (rating > 0 && !mutation.isPending && !mutation.isSuccess)
          mutation.mutate();
      }}
    >
      <fieldset>
        <legend className="text-sm font-medium">Rate this answer</legend>
        <div className="mt-2 flex gap-1">
          {[1, 2, 3, 4, 5].map((value) => (
            <Button
              type="button"
              variant={rating === value ? "default" : "outline"}
              size="sm"
              key={value}
              aria-label={`${value} star rating`}
              onClick={() => setRating(value)}
            >
              {value}
            </Button>
          ))}
        </div>
      </fieldset>
      <label className="block text-sm font-medium">
        Feedback type
        <select
          className="bg-background mt-1 h-10 w-full rounded-lg border px-3"
          value={type}
          onChange={(e) => setType(e.target.value)}
        >
          {types.map((item) => (
            <option key={item}>{item}</option>
          ))}
        </select>
      </label>
      <label className="block text-sm font-medium">
        Optional comment
        <Textarea
          maxLength={2000}
          value={comment}
          onChange={(e) => setComment(e.target.value.replace(/[<>]/g, ""))}
          className="mt-1 min-h-16"
        />
      </label>
      <Button
        size="sm"
        disabled={rating === 0 || mutation.isPending || mutation.isSuccess}
      >
        {mutation.isSuccess
          ? "Submitted"
          : mutation.isPending
            ? "Submitting…"
            : "Submit feedback"}
      </Button>
    </form>
  );
}
