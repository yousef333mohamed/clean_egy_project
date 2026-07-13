"use client";
import { Button } from "@/components/ui/button";
export default function ErrorPage({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="grid min-h-[60vh] place-items-center p-6">
      <div className="max-w-md text-center">
        <h1 className="text-xl font-semibold">This page could not be loaded</h1>
        <p className="text-muted-foreground mt-2">
          Check the backend connection and try again. No operational changes
          were made.
        </p>
        <Button className="mt-5" onClick={reset}>
          Try again
        </Button>
      </div>
    </main>
  );
}
