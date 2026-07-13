import { redirect } from "next/navigation";
import { auth, authEnabled, signIn } from "@/auth";

export default async function SignInPage({ searchParams }: { searchParams: Promise<{ callbackUrl?: string }> }) {
  if (!authEnabled) redirect("/");
  if (await auth()) redirect("/");
  const requested = (await searchParams).callbackUrl;
  const callbackUrl = requested?.startsWith("/") && !requested.startsWith("//") ? requested : "/";
  return (
    <main className="grid min-h-dvh place-items-center p-6">
      <section className="bg-card w-full max-w-md rounded-xl border p-8 shadow-sm">
        <h1 className="text-2xl font-semibold">Sign in to WasteOps</h1>
        <p className="text-muted-foreground mt-2 text-sm">Use your organization identity. WasteOps does not store passwords.</p>
        <form action={async () => { "use server"; await signIn("oidc", { redirectTo: callbackUrl }); }}>
          <button className="bg-primary text-primary-foreground mt-6 w-full rounded-md px-4 py-2 font-medium" type="submit">Continue to identity provider</button>
        </form>
      </section>
    </main>
  );
}
