import { z } from "zod";

const publicEnvSchema = z.object({
  NEXT_PUBLIC_APP_NAME: z.string().min(1),
  NEXT_PUBLIC_API_BASE_URL: z.url(
    "NEXT_PUBLIC_API_BASE_URL must be a valid backend URL",
  ),
  NEXT_PUBLIC_APP_ENV: z.enum(["development", "test", "production"]),
  NEXT_PUBLIC_AUTH_ENABLED: z.enum(["true", "false"]).default("false").transform((value) => value === "true"),
  NEXT_PUBLIC_ENABLE_ADMIN_PAGES: z
    .enum(["true", "false"])
    .transform((value) => value === "true"),
  NEXT_PUBLIC_ENABLE_INGESTION_PAGES: z
    .enum(["true", "false"])
    .transform((value) => value === "true"),
  NEXT_PUBLIC_ENABLE_EVALUATION_PAGES: z
    .enum(["true", "false"])
    .transform((value) => value === "true"),
  NEXT_PUBLIC_ENABLE_PROMPT_PAGES: z
    .enum(["true", "false"])
    .transform((value) => value === "true"),
  NEXT_PUBLIC_DEFAULT_LANGUAGE: z.string().min(2),
  NEXT_PUBLIC_DEFAULT_TIMEZONE: z.string().min(1),
});

const result = publicEnvSchema.safeParse({
  NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME,
  NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
  NEXT_PUBLIC_APP_ENV: process.env.NEXT_PUBLIC_APP_ENV,
  NEXT_PUBLIC_AUTH_ENABLED: process.env.NEXT_PUBLIC_AUTH_ENABLED,
  NEXT_PUBLIC_ENABLE_ADMIN_PAGES: process.env.NEXT_PUBLIC_ENABLE_ADMIN_PAGES,
  NEXT_PUBLIC_ENABLE_INGESTION_PAGES:
    process.env.NEXT_PUBLIC_ENABLE_INGESTION_PAGES,
  NEXT_PUBLIC_ENABLE_EVALUATION_PAGES:
    process.env.NEXT_PUBLIC_ENABLE_EVALUATION_PAGES,
  NEXT_PUBLIC_ENABLE_PROMPT_PAGES: process.env.NEXT_PUBLIC_ENABLE_PROMPT_PAGES,
  NEXT_PUBLIC_DEFAULT_LANGUAGE: process.env.NEXT_PUBLIC_DEFAULT_LANGUAGE,
  NEXT_PUBLIC_DEFAULT_TIMEZONE: process.env.NEXT_PUBLIC_DEFAULT_TIMEZONE,
});

if (!result.success) {
  throw new Error(
    `Invalid public frontend environment: ${result.error.issues.map((issue) => `${issue.path.join(".")}: ${issue.message}`).join("; ")}`,
  );
}

export const env = result.data;
