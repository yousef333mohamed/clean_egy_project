import type { Metadata } from "next";
import "./globals.css";
import { env } from "@/lib/env";
import { AppProviders } from "@/providers/app-providers";

export const metadata: Metadata = {
  title: {
    default: env.NEXT_PUBLIC_APP_NAME,
    template: `%s | ${env.NEXT_PUBLIC_APP_NAME}`,
  },
  description: "Evidence-grounded waste operations management dashboard",
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const direction = env.NEXT_PUBLIC_DEFAULT_LANGUAGE === "ar" ? "rtl" : "ltr";
  return (
    <html
      lang={env.NEXT_PUBLIC_DEFAULT_LANGUAGE}
      dir={direction}
      suppressHydrationWarning
    >
      <body>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
