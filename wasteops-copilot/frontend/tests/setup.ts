import "@testing-library/jest-dom/vitest";
import { vi } from "vitest";

process.env.NEXT_PUBLIC_APP_NAME = "WasteOps Decision Intelligence Copilot";
process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";
process.env.NEXT_PUBLIC_APP_ENV = "test";
process.env.NEXT_PUBLIC_ENABLE_ADMIN_PAGES = "true";
process.env.NEXT_PUBLIC_ENABLE_INGESTION_PAGES = "true";
process.env.NEXT_PUBLIC_ENABLE_EVALUATION_PAGES = "true";
process.env.NEXT_PUBLIC_ENABLE_PROMPT_PAGES = "true";
process.env.NEXT_PUBLIC_DEFAULT_LANGUAGE = "en";
process.env.NEXT_PUBLIC_DEFAULT_TIMEZONE = "Africa/Cairo";

Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi
    .fn()
    .mockImplementation(() => ({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
});
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
vi.stubGlobal("ResizeObserver", ResizeObserverMock);
