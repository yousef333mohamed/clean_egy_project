import { describe, expect, it } from "vitest";
import { parseCitations } from "@/lib/citations";
import { formatDate, formatDuration, formatValue } from "@/lib/formatting";
import { ragResponseSchema } from "@/lib/schemas/api";

describe("safe utilities", () => {
  it("preserves null rather than turning it into zero", () =>
    expect(formatValue(null)).toBe("Not available"));
  it("formats durations and invalid dates safely", () => {
    expect(formatDuration(1500)).toBe("1.50 s");
    expect(formatDate("not-a-date")).toBe("not-a-date");
  });
  it("parses all evidence namespaces without changing identifiers", () =>
    expect(
      parseCitations("See [S1], [D2], [R3], [M4].").map((item) => item.kind),
    ).toEqual(["document", "database", "rule", "model"]));
  it("rejects a structurally invalid RAG response", () =>
    expect(ragResponseSchema.safeParse({ answer: "unsupported" }).success).toBe(
      false,
    ));
});
