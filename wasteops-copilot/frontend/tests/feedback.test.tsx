import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { FeedbackForm } from "@/components/feedback/feedback-form";
describe("feedback", () => {
  it("requires a rating before submission", () => {
    render(
      <QueryClientProvider client={new QueryClient()}>
        <FeedbackForm requestId="req-1" />
      </QueryClientProvider>,
    );
    expect(
      screen.getByRole("button", { name: "Submit feedback" }),
    ).toBeDisabled();
    expect(screen.getByLabelText("Optional comment")).toHaveAttribute(
      "maxlength",
      "2000",
    );
  });
});
