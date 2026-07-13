import { Button } from "@/components/ui/button";
const suggestions = [
  "What is the procedure for a missed collection?",
  "How many critical bins are in the latest data?",
  "Combine recent missed collections with escalation guidance.",
  "Which bins should receive manager attention first?",
];
export function SuggestedQuestions({
  onSelect,
}: {
  onSelect: (value: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2" aria-label="Suggested questions">
      {suggestions.map((item) => (
        <Button
          key={item}
          variant="outline"
          size="sm"
          onClick={() => onSelect(item)}
        >
          {item}
        </Button>
      ))}
    </div>
  );
}
