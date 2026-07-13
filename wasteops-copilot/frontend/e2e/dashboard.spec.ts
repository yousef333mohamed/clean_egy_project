import { expect, test, type Page } from "@playwright/test";

const evidence = {
  evidence_id: "D1",
  source_type: "database",
  tool_name: "get_operational_overview",
  metric: null,
  description: "Operational overview",
  filters: {},
  columns: ["total_bins", "latest_critical_bins"],
  rows: [
    {
      total_bins: 100,
      latest_critical_bins: 7,
      latest_low_battery_bins: 3,
      latest_sensor_fault_bins: 2,
      bin_status_effective_timestamp: "2026-07-13T10:00:00Z",
      missed_collection_count: 4,
      emergency_request_count: 1,
      complaint_count: 5,
      operations_effective_date: "2026-07-13",
      trip_count: 20,
      trucks_effective_date: "2026-07-13",
      attendance_rate_pct: 94.5,
      workforce_effective_date: "2026-07-13",
    },
  ],
  record_count: 1,
  data_period: { start: null, end: null },
  generated_at: "2026-07-13T10:00:00Z",
  notes: ["Configured thresholds are not official policy."],
  aggregation_definitions: {},
};
async function mockBackend(page: Page) {
  await page.route("http://localhost:8000/api/**", async (route) => {
    const url = route.request().url();
    let body: unknown = {
      status: "ok",
      service: "WasteOps",
      environment: "test",
    };
    if (url.endsWith("/health/database"))
      body = { status: "healthy", database: "connected" };
    else if (url.includes("analytics/tools/")) body = evidence;
    else if (url.endsWith("/chat/rag"))
      body = {
        answer: "Use the documented procedure [S1].",
        grounded: true,
        insufficient_context: false,
        citations: [
          {
            citation_id: "S1",
            document_id: "doc-1",
            chunk_id: "chunk-1",
            source_filename: "procedure.md",
            document_title: "Procedure",
            page_number: 1,
            section_title: "Response",
            chunk_number: 1,
            content_preview: "Safe preview",
            is_synthetic: true,
          },
        ],
        retrieved_evidence_count: 1,
        used_evidence_count: 1,
        warnings: ["Synthetic demo document"],
        query: "procedure",
        rewritten_query: null,
        filters_applied: {},
        request_id: "123e4567-e89b-12d3-a456-426614174000",
        debug: null,
      };
    else if (url.endsWith("/chat/hybrid"))
      body = {
        answer: "Operational fact [D1] with guidance [S1].",
        route: "HYBRID_ANALYSIS",
        grounded: true,
        insufficient_data: false,
        insufficient_context: false,
        database_evidence: [evidence],
        document_citations: [],
        warnings: [],
        request_id: "123e4567-e89b-12d3-a456-426614174003",
      };
    else if (url.endsWith("/analytics/query"))
      body = {
        answer: "There are 7 critical bins [D1].",
        route: "STRUCTURED_DATA",
        tool_name: "list_critical_bins",
        domain: "BINS",
        grounded: true,
        insufficient_data: false,
        database_evidence: [evidence],
        citations: [
          {
            citation_id: "D1",
            source_type: "database",
            tool_name: "list_critical_bins",
            description: "Critical bins",
          },
        ],
        warnings: [],
        request_id: "123e4567-e89b-12d3-a456-426614174001",
        debug: null,
      };
    else if (url.endsWith("/decisions/recommend"))
      body = {
        request_id: "123e4567-e89b-12d3-a456-426614174002",
        decision_type: "BIN_ATTENTION_PRIORITY",
        situation_summary: "Seven bins require manager review.",
        recommended_option: null,
        alternative_options: [],
        database_evidence: [],
        document_citations: [],
        confidence: {
          score: 0.4,
          level: "LOW",
          components: {
            retrieval_coverage: 0.4,
            source_quality: 0.4,
            data_completeness: 0.4,
            source_agreement: 0.4,
            recency: 0.4,
          },
          explanation: "Limited evidence",
        },
        missing_information: ["Official procedure"],
        warnings: [],
        requires_human_approval: true,
        grounded: false,
        insufficient_context: true,
      };
    else if (url.endsWith("/feedback"))
      body = {
        id: "123e4567-e89b-12d3-a456-426614174099",
        request_id: "123e4567-e89b-12d3-a456-426614174000",
        rating: 5,
        feedback_type: "HELPFUL",
        created_at: "2026-07-13T10:00:00Z",
      };
    else if (url.endsWith("/ingestion/files"))
      body = [
        {
          dataset: "smart_bins",
          filename: "smart_bins.csv",
          size_bytes: 100,
          available: true,
        },
      ];
    else if (url.includes("/ingestion/validate/"))
      body = {
        run_id: "123e4567-e89b-12d3-a456-426614174010",
        dataset: "smart_bins",
        source_filename: "smart_bins.csv",
        status: "DRY_RUN_COMPLETED",
        dry_run: true,
        total_rows: 10,
        valid_rows: 10,
        inserted_rows: 0,
        duplicate_rows: 0,
        rejected_rows: 0,
        failed_rows: 0,
        warnings: [],
        rejection_report: null,
        started_at: "2026-07-13T10:00:00Z",
        completed_at: "2026-07-13T10:00:01Z",
        duration_seconds: 1,
        error_message: null,
      };
    else if (url.endsWith("/documents/files")) body = [];
    else if (url.endsWith("/evaluation/datasets"))
      body = [
        {
          name: "wasteops_rag_v1",
          type: "rag",
          path: "rag/wasteops_rag_v1.json",
          version: "1.0.0",
        },
      ];
    else if (url.endsWith("/evaluation/runs"))
      body = {
        run_id: "123e4567-e89b-12d3-a456-426614174020",
        status: "COMPLETED",
        metrics: { groundedness: 1 },
        critical_failures: 0,
      };
    else if (url.includes("/quality-gate"))
      body = {
        passed: true,
        metrics: { groundedness: 1, numeric_error_rate: 0 },
        failed_rules: [],
        critical_failures: 0,
      };
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(body),
    });
  });
}

test.beforeEach(async ({ page }) => mockBackend(page));
test("opens dashboard and reports backend connection", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Operations overview" }),
  ).toBeVisible();
  await expect(page.getByText("100")).toBeVisible();
  await expect(page.getByText("Connected")).toBeVisible();
});
test("switches to dark mode with an accessible control", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "light" });
  await page.goto("/");
  await page.getByLabel("Toggle color theme").click();
  await expect(page.locator("html")).toHaveClass(/dark/);
});
test("asks a RAG question, opens citation, and submits feedback", async ({
  page,
}) => {
  await page.goto("/assistant");
  await page.getByLabel("Ask WasteOps").fill("What is the procedure?");
  await page.getByLabel("Submit question").click();
  await expect(page.getByText(/documented procedure/)).toBeVisible();
  await page.getByLabel("Open S1 evidence").click();
  await expect(page.getByText("Synthetic status")).toBeVisible();
  await page.getByLabel("Close dialog").click();
  await page.getByLabel("5 star rating").click();
  await page.getByRole("button", { name: "Submit feedback" }).click();
  await expect(page.getByText("Submitted")).toBeVisible();
});
test("runs analytics and displays database evidence", async ({ page }) => {
  await page.goto("/analytics");
  await page.getByLabel("Operational question").fill("Show critical bins");
  await page.getByRole("button", { name: "Run analytics" }).click();
  await expect(page.getByText(/7 critical bins/)).toBeVisible();
  await expect(
    page.getByRole("columnheader", { name: /total_bins/i }),
  ).toBeVisible();
});
test("asks a hybrid question without silently changing mode", async ({
  page,
}) => {
  await page.goto("/assistant");
  await page.getByRole("radio", { name: "Hybrid" }).click();
  await page.getByLabel("Ask WasteOps").fill("Combine facts and guidance");
  await page.getByLabel("Submit question").click();
  await expect(page.getByText(/Operational fact/)).toBeVisible();
  await expect(page.getByText(/Active mode:/)).toContainText("Hybrid");
});
test("generates decision support with human approval and no execute action", async ({
  page,
}) => {
  await page.goto("/decisions");
  await page.getByLabel("Decision question").fill("Which bins need attention?");
  await page.getByRole("button", { name: "Generate recommendation" }).click();
  await expect(page.getByText("Human approval required")).toBeVisible();
  await expect(page.getByText(/not the probability/i)).toBeVisible();
  await expect(page.getByRole("button", { name: /execute/i })).toHaveCount(0);
});
test("views bin and truck transparent rule alerts", async ({ page }) => {
  await page.goto("/bins?tab=critical");
  await expect(page.getByText(/configured operational rules/i)).toBeVisible();
  await page.goto("/trucks");
  await expect(page.getByText("Transparent rule-based alert")).toBeVisible();
});
test("validates an allow-listed ingestion file with confirmation", async ({
  page,
}) => {
  await page.goto("/ingestion");
  await expect(page.getByText("smart_bins.csv")).toBeVisible();
  await page.getByRole("button", { name: "Validate" }).first().click();
  await expect(
    page.getByText("Validation does not insert records."),
  ).toBeVisible();
  await page.getByRole("button", { name: "Confirm validate" }).click();
});
test("views deterministic evaluation quality gate", async ({ page }) => {
  await page.goto("/system/evaluations");
  await page.getByRole("button", { name: "Run with fake providers" }).click();
  await expect(page.getByText("Passed")).toBeVisible();
  await expect(page.getByText("Critical failures: 0")).toBeVisible();
});
