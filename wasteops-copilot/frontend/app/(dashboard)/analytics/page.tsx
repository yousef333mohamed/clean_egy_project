"use client";
import { useState } from "react";
import type { AnalyticsResponse } from "@/lib/schemas/api";
import { PageHeader } from "@/components/layout/page-header";
import { AnalyticsQueryForm } from "@/components/analytics/analytics-query-form";
import { AnalyticsResults } from "@/components/analytics/analytics-results";
export default function AnalyticsPage() {
  const [result, setResult] = useState<AnalyticsResponse | null>(null);
  return (
    <>
      <PageHeader
        title="Natural-language analytics"
        description="Questions are routed to approved read-only backend tools. Table sorting only changes this local view."
      />
      <div className="space-y-6">
        <AnalyticsQueryForm onResult={setResult} />
        {result && <AnalyticsResults result={result} />}
      </div>
    </>
  );
}
