export default function AuthErrorPage() {
  return <main className="grid min-h-dvh place-items-center p-6"><section role="alert" className="max-w-md rounded-lg border p-6"><h1 className="text-xl font-semibold">Sign-in could not be completed</h1><p className="text-muted-foreground mt-2">Try again or contact your administrator. No credentials were stored by WasteOps.</p><a className="mt-4 inline-block underline" href="/auth/signin">Return to sign in</a></section></main>;
}
