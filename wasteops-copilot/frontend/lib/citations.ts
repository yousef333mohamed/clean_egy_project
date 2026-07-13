export type CitationKind = "document" | "database" | "rule" | "model";
export interface ParsedCitation {
  id: string;
  kind: CitationKind;
  start: number;
  end: number;
}
const kinds: Record<string, CitationKind> = {
  S: "document",
  D: "database",
  R: "rule",
  M: "model",
};
export function parseCitations(text: string): ParsedCitation[] {
  return [...text.matchAll(/\[([SDRM]\d+)\]/g)].map((match) => ({
    id: match[1],
    kind: kinds[match[1][0]],
    start: match.index ?? 0,
    end: (match.index ?? 0) + match[0].length,
  }));
}
