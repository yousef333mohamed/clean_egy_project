"use client";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { previewDecision, recommendDecision } from "@/lib/api/decisions";
import { userErrorMessage } from "@/lib/api/errors";
import type { DecisionResponse } from "@/lib/schemas/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
const schema = z
  .object({
    question: z.string().trim().min(3).max(4000),
    region: z.string().max(120),
    governorate: z.string().max(120),
    binIds: z.string(),
    truckIds: z.string(),
    workerIds: z.string(),
    startDate: z.string(),
    endDate: z.string(),
    maximumActions: z.coerce.number().int().min(2).max(10),
    latest: z.boolean(),
    continuity: z.boolean(),
    safety: z.literal(true),
    cost: z.boolean(),
  })
  .refine(
    (data) =>
      !data.startDate || !data.endDate || data.startDate <= data.endDate,
    { path: ["endDate"], message: "End date must follow start date" },
  );
type FormValues = z.infer<typeof schema>;
function request(values: FormValues) {
  const ids = (value: string) =>
    value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  return {
    question: values.question,
    scope: {
      region: values.region || null,
      governorate: values.governorate || null,
      bin_ids: ids(values.binIds),
      truck_ids: ids(values.truckIds),
      worker_ids: ids(values.workerIds),
      start_date: values.startDate || null,
      end_date: values.endDate || null,
      use_latest_available_data: values.latest,
    },
    constraints: {
      maximum_actions: values.maximumActions,
      prioritize_service_continuity: values.continuity,
      prioritize_safety: true,
      prioritize_cost_reduction: values.cost,
    },
  };
}
export function DecisionRequestForm({
  onResult,
}: {
  onResult: (result: DecisionResponse) => void;
}) {
  const form = useForm<z.input<typeof schema>, unknown, FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      question: "",
      region: "",
      governorate: "",
      binIds: "",
      truckIds: "",
      workerIds: "",
      startDate: "",
      endDate: "",
      maximumActions: 4,
      latest: true,
      continuity: true,
      safety: true,
      cost: false,
    },
  });
  const preview = useMutation({
    mutationFn: (values: FormValues) => previewDecision(request(values)),
    onSuccess: (data) =>
      toast.info(
        `Preview ready: ${String(data.route.decision_type ?? "route detected")}`,
      ),
    onError: (e) => toast.error(userErrorMessage(e)),
  });
  const recommend = useMutation({
    mutationFn: (values: FormValues) => recommendDecision(request(values)),
    onSuccess: onResult,
    onError: (e) => toast.error(userErrorMessage(e)),
  });
  const field = (
    name: keyof FormValues,
    label: string,
    placeholder?: string,
  ) => (
    <label className="text-sm font-medium">
      {label}
      <Input
        className="mt-1"
        placeholder={placeholder}
        {...form.register(name)}
      />
      {form.formState.errors[name] && (
        <span className="text-destructive text-xs">
          {form.formState.errors[name]?.message}
        </span>
      )}
    </label>
  );
  return (
    <form
      className="space-y-5"
      onSubmit={form.handleSubmit((values) => recommend.mutate(values))}
    >
      <label className="block text-sm font-medium">
        Decision question
        <Textarea
          className="mt-1"
          {...form.register("question")}
          placeholder="Which bins should receive manager attention first?"
        />
        {form.formState.errors.question && (
          <span className="text-destructive text-xs">
            {form.formState.errors.question.message}
          </span>
        )}
      </label>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {field("region", "Region")}
        {field("governorate", "Governorate")}
        {field("binIds", "Bin IDs", "BIN-001, BIN-002")}
        {field("truckIds", "Truck IDs", "TRUCK-014")}
        {field("workerIds", "Worker IDs", "WORKER-010")}
        {field("maximumActions", "Maximum actions")}
        {field("startDate", "Start date")}
        {field("endDate", "End date")}
      </div>
      <fieldset className="grid gap-3 rounded-xl border p-4 sm:grid-cols-2">
        <legend className="px-2 text-sm font-medium">Safe preferences</legend>
        <Check label="Use latest available data" {...form.register("latest")} />
        <Check
          label="Prioritize service continuity"
          {...form.register("continuity")}
        />
        <Check label="Prioritize safety (required)" disabled checked readOnly />
        <Check label="Prioritize cost reduction" {...form.register("cost")} />
      </fieldset>
      <div className="flex gap-2">
        <Button
          type="button"
          variant="outline"
          disabled={preview.isPending || recommend.isPending}
          onClick={form.handleSubmit((values) => preview.mutate(values))}
        >
          Preview evidence plan
        </Button>
        <Button disabled={recommend.isPending || preview.isPending}>
          {recommend.isPending
            ? "Analyzing evidence…"
            : "Generate recommendation"}
        </Button>
      </div>
    </form>
  );
}
function Check({
  label,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  return (
    <label className="flex items-center gap-2 text-sm">
      <input type="checkbox" className="accent-primary size-4" {...props} />
      {label}
    </label>
  );
}
