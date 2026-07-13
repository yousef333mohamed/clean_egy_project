"use client";
import { useState } from "react";
import type { DecisionResponse } from "@/lib/schemas/api";
import { PageHeader } from "@/components/layout/page-header";
import { DecisionRequestForm } from "@/components/decisions/decision-request-form";
import { DecisionSummary } from "@/components/decisions/decision-summary";
export default function DecisionsPage() {
  const [result, setResult] = useState<DecisionResponse | null>(null);
  return (
    <>
      <PageHeader
        title="Decision Intelligence"
        description="Collect evidence, compare safe options, and generate manager-reviewed recommendations. This interface cannot execute actions."
      />
      <div className="space-y-8">
        <DecisionRequestForm onResult={setResult} />
        {result && <DecisionSummary result={result} />}
      </div>
    </>
  );
}
