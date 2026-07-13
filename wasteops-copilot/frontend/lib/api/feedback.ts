import { apiPost } from "@/lib/api/client";
import { feedbackResponseSchema } from "@/lib/schemas/api";
export const submitFeedback = (
  body: {
    request_id?: string;
    rating: number;
    feedback_type: string;
    comment?: string;
  },
  signal?: AbortSignal,
) => apiPost("/api/feedback", body, feedbackResponseSchema, signal);
