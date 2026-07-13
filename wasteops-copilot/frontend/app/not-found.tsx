import Link from "next/link";
export default function NotFound() {
  return (
    <main className="grid min-h-dvh place-items-center">
      <div className="text-center">
        <h1 className="text-2xl font-semibold">Page not found</h1>
        <Link className="text-primary mt-4 inline-block underline" href="/">
          Return to overview
        </Link>
      </div>
    </main>
  );
}
