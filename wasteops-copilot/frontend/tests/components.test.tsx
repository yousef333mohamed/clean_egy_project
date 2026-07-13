import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Battery } from "lucide-react";
import { MetricCard } from "@/components/dashboard/metric-card";
import { HumanApprovalBanner } from "@/components/decisions/human-approval-banner";
import { ConfidenceBreakdown } from "@/components/decisions/confidence-breakdown";
import { DocumentStatusBadge } from "@/components/documents/document-status-badge";
import { ChatInput } from "@/components/assistant/chat-input";
import { AnalyticsTable } from "@/components/analytics/analytics-table";
import { StatePanel } from "@/components/shared/state-panel";
import { RecommendationCard } from "@/components/decisions/recommendation-card";
import { AlternativeOptions } from "@/components/decisions/alternative-options";
import { SourceCitation } from "@/components/assistant/source-citation";
import { ConfirmationAction } from "@/components/ingestion/confirmation-action";

const option = {
  option_id: "O1",
  action_category: "INSPECT",
  title: "Inspect the bin",
  action: "Review sensor and fill state",
  supporting_evidence_ids: ["D1"],
  assumptions: [],
  operational_requirements: [],
  expected_impact: ["Verify current state"],
  possible_risks: [],
  priority: "HIGH",
  score: 0.75,
  score_breakdown: {
    service_impact: 0.8,
    urgency: 0.7,
    risk_control: 0.8,
    feasibility: 0.7,
    policy_alignment: 0.75,
  },
  risks: [],
  trade_offs: [],
};

describe("operations components", () => {
  it("renders a metric no-data state exactly", () => {
    render(<MetricCard label="Battery" value={null} icon={Battery} />);
    expect(screen.getByText("Not available")).toBeInTheDocument();
  });
  it("always explains human approval", () => {
    render(<HumanApprovalBanner />);
    expect(
      screen.getByText(/authorized operations manager/i),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /execute/i }),
    ).not.toBeInTheDocument();
  });
  it("explains confidence as evidence quality", () => {
    render(
      <ConfidenceBreakdown
        confidence={{
          score: 0.5,
          level: "MEDIUM",
          explanation: "Evidence coverage",
          components: {
            retrieval_coverage: 0.5,
            source_quality: 0.5,
            data_completeness: 0.5,
            source_agreement: 0.5,
          recency: 0.5,
          model_reliability: 0.5,
          },
        }}
      />,
    );
    expect(screen.getByText(/not the probability/i)).toBeInTheDocument();
  });
  it("labels synthetic documents", () => {
    render(
      <DocumentStatusBadge
        synthetic
        authority="demo_only"
        active
        status="COMPLETED"
      />,
    );
    expect(screen.getByText("Synthetic demo")).toBeInTheDocument();
  });
  it("supports enter submission and shift-enter", async () => {
    const submit = vi.fn();
    const user = userEvent.setup();
    render(
      <ChatInput
        value="question"
        onChange={vi.fn()}
        onSubmit={submit}
        onCancel={vi.fn()}
        pending={false}
      />,
    );
    const input = screen.getByLabelText("Ask WasteOps");
    await user.type(input, "{shift>}{enter}{/shift}");
    expect(submit).not.toHaveBeenCalled();
    await user.type(input, "{enter}");
    expect(submit).toHaveBeenCalledOnce();
  });
  it("renders accessible analytics headers and nulls", () => {
    render(
      <AnalyticsTable
        columns={["region", "value"]}
        rows={[{ region: "Delta", value: null }]}
      />,
    );
    expect(
      screen.getByRole("columnheader", { name: /region/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("Not available")).toBeInTheDocument();
  });
  it("renders reusable safe error state", () => {
    render(
      <StatePanel
        kind="error"
        title="Backend unavailable"
        description="Retry safely"
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Retry safely");
  });
  it("is direction-inheritable for RTL preparation", () => {
    const { container } = render(
      <div dir="rtl">
        <MetricCard label="الحاويات" value={3} icon={Battery} />
      </div>,
    );
    expect(container.firstElementChild).toHaveAttribute("dir", "rtl");
  });
  it("renders backend decision scores without calling them probabilities", () => {
    render(<RecommendationCard option={option} />);
    expect(
      screen.getByText(/Deterministic decision score/),
    ).toBeInTheDocument();
    expect(screen.getByText(/not a probability/i)).toBeInTheDocument();
  });
  it("keeps alternative options collapsed by default", () => {
    render(<AlternativeOptions options={[option]} />);
    expect(
      screen.getByText(/Inspect the bin/).closest("details"),
    ).not.toHaveAttribute("open");
  });
  it("opens a bounded database evidence dialog", async () => {
    const user = userEvent.setup();
    render(
      <SourceCitation
        id="D1"
        database={{
          evidence_id: "D1",
          source_type: "database",
          tool_name: "safe_tool",
          metric: null,
          description: "Evidence",
          filters: {},
          columns: ["value"],
          rows: [{ value: 2 }],
          record_count: 1,
          data_period: { start: null, end: null },
          generated_at: "2026-01-01",
          notes: [],
          aggregation_definitions: {},
        }}
      />,
    );
    await user.click(screen.getByLabelText("Open D1 evidence"));
    expect(
      screen.getByText(
        "Backend-supplied evidence summary. SQL, embeddings, and full documents are never displayed.",
      ),
    ).toBeInTheDocument();
  });
  it("requires confirmation before ingestion actions", async () => {
    const user = userEvent.setup();
    const confirm = vi.fn();
    render(
      <ConfirmationAction
        label="Ingest"
        title="Confirm ingestion"
        description="Writes audited rows"
        pending={false}
        onConfirm={confirm}
      />,
    );
    await user.click(screen.getByRole("button", { name: "Ingest" }));
    expect(confirm).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Confirm ingest" }));
    expect(confirm).toHaveBeenCalledOnce();
  });
});
