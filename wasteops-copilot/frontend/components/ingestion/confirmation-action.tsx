"use client";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
export function ConfirmationAction({
  label,
  title,
  description,
  pending,
  onConfirm,
}: {
  label: string;
  title: string;
  description: string;
  pending: boolean;
  onConfirm: () => void;
}) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button size="sm" variant={label === "Ingest" ? "default" : "outline"}>
          {label}
        </Button>
      </DialogTrigger>
      <DialogContent title={title} description={description}>
        <p className="text-muted-foreground text-sm">
          Only allow-listed files discovered by the backend can be processed.
          Complete stack traces are not displayed.
        </p>
        <Button className="mt-5" disabled={pending} onClick={onConfirm}>
          {pending ? "Processing…" : `Confirm ${label.toLowerCase()}`}
        </Button>
      </DialogContent>
    </Dialog>
  );
}
