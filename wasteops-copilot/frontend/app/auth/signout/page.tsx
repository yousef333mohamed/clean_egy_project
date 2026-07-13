import { signOut } from "@/auth";

export default function SignOutPage() {
  return <main className="grid min-h-dvh place-items-center"><form action={async () => { "use server"; await signOut({ redirectTo: "/auth/signin" }); }}><button className="bg-primary text-primary-foreground rounded-md px-4 py-2" type="submit">Confirm sign out</button></form></main>;
}
