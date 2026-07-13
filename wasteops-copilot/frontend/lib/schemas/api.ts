import { z } from "zod";

export const healthSchema = z.object({
  status: z.string(),
  service: z.string().optional(),
  environment: z.string().optional(),
  database: z.string().optional(),
});
export const dataPeriodSchema = z.object({
  start: z.string().nullable(),
  end: z.string().nullable(),
});
export const evidenceSchema = z.object({
  evidence_id: z.string(),
  source_type: z.string(),
  tool_name: z.string(),
  metric: z.string().nullable(),
  description: z.string(),
  filters: z.record(z.string(), z.unknown()),
  columns: z.array(z.string()),
  rows: z.array(z.record(z.string(), z.unknown())),
  record_count: z.number().int().nonnegative(),
  data_period: dataPeriodSchema,
  generated_at: z.string(),
  notes: z.array(z.string()),
  aggregation_definitions: z.record(z.string(), z.string()),
});
export const citationSchema = z.object({
  citation_id: z.string(),
  document_id: z.string(),
  chunk_id: z.string(),
  source_filename: z.string(),
  document_title: z.string(),
  page_number: z.number().int().nullable(),
  section_title: z.string().nullable(),
  chunk_number: z.number().int(),
  content_preview: z.string(),
  is_synthetic: z.boolean(),
});
export const databaseCitationSchema = z.object({
  citation_id: z.string(),
  source_type: z.string(),
  tool_name: z.string(),
  description: z.string(),
});
export const ragResponseSchema = z.object({
  answer: z.string(),
  grounded: z.boolean(),
  insufficient_context: z.boolean(),
  citations: z.array(citationSchema),
  retrieved_evidence_count: z.number(),
  used_evidence_count: z.number(),
  warnings: z.array(z.string()),
  query: z.string(),
  rewritten_query: z.string().nullable(),
  filters_applied: z.record(z.string(), z.unknown()),
  request_id: z.uuid(),
  debug: z.record(z.string(), z.unknown()).nullable().optional(),
});
export const analyticsResponseSchema = z.object({
  answer: z.string(),
  route: z.string(),
  tool_name: z.string().nullable(),
  domain: z.string().nullable(),
  grounded: z.boolean(),
  insufficient_data: z.boolean(),
  database_evidence: z.array(evidenceSchema),
  citations: z.array(databaseCitationSchema),
  warnings: z.array(z.string()),
  request_id: z.uuid(),
  debug: z.record(z.string(), z.unknown()).nullable().optional(),
});
export const hybridResponseSchema = z.object({
  answer: z.string(),
  route: z.string(),
  grounded: z.boolean(),
  insufficient_data: z.boolean(),
  insufficient_context: z.boolean(),
  database_evidence: z.array(evidenceSchema),
  document_citations: z.array(citationSchema),
  warnings: z.array(z.string()),
  request_id: z.uuid(),
});
const scoreBreakdownSchema = z.object({
  service_impact: z.number(),
  urgency: z.number(),
  risk_control: z.number(),
  feasibility: z.number(),
  policy_alignment: z.number(),
});
const riskSchema = z.object({
  risk_id: z.string(),
  category: z.string(),
  description: z.string(),
  severity: z.string(),
  likelihood: z.string(),
  supporting_evidence_ids: z.array(z.string()),
  mitigation: z.string(),
});
export const optionSchema = z.object({
  option_id: z.string(),
  action_category: z.string(),
  title: z.string(),
  action: z.string(),
  supporting_evidence_ids: z.array(z.string()),
  assumptions: z.array(z.string()),
  operational_requirements: z.array(z.string()),
  expected_impact: z.array(z.string()),
  possible_risks: z.array(z.string()),
  priority: z.string(),
  score: z.number(),
  score_breakdown: scoreBreakdownSchema,
  risks: z.array(riskSchema),
  trade_offs: z.array(z.string()),
});
export const confidenceSchema = z.object({
  score: z.number(),
  level: z.string(),
  components: z.object({
    retrieval_coverage: z.number(),
    source_quality: z.number(),
    data_completeness: z.number(),
    source_agreement: z.number(),
    recency: z.number(),
  }),
  explanation: z.string(),
});
export const decisionResponseSchema = z.object({
  request_id: z.uuid(),
  decision_type: z.string(),
  situation_summary: z.string(),
  recommended_option: optionSchema.nullable(),
  alternative_options: z.array(optionSchema),
  database_evidence: z.array(evidenceSchema),
  document_citations: z.array(citationSchema),
  confidence: confidenceSchema,
  missing_information: z.array(z.string()),
  warnings: z.array(z.string()),
  requires_human_approval: z.literal(true),
  grounded: z.boolean(),
  insufficient_context: z.boolean(),
});
export const previewResponseSchema = z.object({
  route: z.record(z.string(), z.unknown()),
  plan: z.record(z.string(), z.unknown()),
});
export const documentSchema = z.object({
  document_id: z.string(),
  source_filename: z.string(),
  relative_path: z.string(),
  file_extension: z.string(),
  mime_type: z.string(),
  document_type: z.string().nullable(),
  department: z.string().nullable(),
  asset_type: z.string().nullable(),
  region: z.string().nullable(),
  effective_date: z.string().nullable(),
  version: z.string().nullable(),
  language: z.string(),
  is_synthetic: z.boolean().nullable(),
  authority_level: z.string(),
  expiration_date: z.string().nullable(),
  title: z.string(),
  file_size_bytes: z.number(),
  status: z.string(),
  total_pages: z.number(),
  total_characters: z.number(),
  total_tokens: z.number(),
  total_chunks: z.number(),
  is_active: z.boolean(),
  created_at: z.string(),
  updated_at: z.string(),
  metadata_json: z.record(z.string(), z.unknown()),
});
export const documentPageSchema = z.object({
  items: z.array(documentSchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
});
export const ingestionResultSchema = z.object({
  run_id: z.uuid(),
  dataset: z.string(),
  source_filename: z.string(),
  status: z.string(),
  dry_run: z.boolean(),
  total_rows: z.number(),
  valid_rows: z.number(),
  inserted_rows: z.number(),
  duplicate_rows: z.number(),
  rejected_rows: z.number(),
  failed_rows: z.number(),
  warnings: z.array(z.string()),
  rejection_report: z.string().nullable(),
  started_at: z.string(),
  completed_at: z.string(),
  duration_seconds: z.number(),
  error_message: z.string().nullable(),
});
export const feedbackResponseSchema = z.object({
  id: z.uuid(),
  request_id: z.string().nullable(),
  rating: z.number().min(1).max(5),
  feedback_type: z.string(),
  created_at: z.string(),
});
export const evaluationRunStartSchema = z.object({
  run_id: z.string(),
  status: z.string(),
  metrics: z.record(z.string(), z.number()),
  critical_failures: z.number(),
});

export type OperationalEvidence = z.infer<typeof evidenceSchema>;
export type Citation = z.infer<typeof citationSchema>;
export type RAGResponse = z.infer<typeof ragResponseSchema>;
export type AnalyticsResponse = z.infer<typeof analyticsResponseSchema>;
export type HybridResponse = z.infer<typeof hybridResponseSchema>;
export type DecisionResponse = z.infer<typeof decisionResponseSchema>;
export type DecisionOption = z.infer<typeof optionSchema>;
