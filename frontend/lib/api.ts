// Thin typed client over the backend. Requests go to /api/* which Next rewrites
// to the FastAPI server (see next.config.mjs).
import type {
  Automation,
  AutomationRunResult,
  BulkActionResult,
  BulkActionType,
  Category,
  Email,
  EmailDetail,
  EmailPage,
  Health,
  Insights,
  LearningStatus,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json())?.detail ?? detail;
    } catch {
      /* body was not json */
    }
    throw new Error(typeof detail === "string" ? detail : "Request failed");
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export interface EmailQuery {
  category?: string | null;
  unread?: boolean | null;
  archived?: boolean | null;
  search?: string | null;
  limit?: number;
  offset?: number;
}

function qs(params: Record<string, unknown>): string {
  const usp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") usp.set(k, String(v));
  }
  const s = usp.toString();
  return s ? `?${s}` : "";
}

export const api = {
  health: () => request<Health>("/health"),

  emails: (q: EmailQuery = {}) => request<EmailPage>(`/emails${qs({ ...q })}`),
  email: (id: number) => request<EmailDetail>(`/emails/${id}`),

  categories: () => request<Category[]>("/categories"),
  insights: () => request<Insights>("/insights"),
  learningStatus: () => request<LearningStatus>("/learning/status"),

  correct: (emailId: number, toCategory: string) =>
    request("/corrections", {
      method: "POST",
      body: JSON.stringify({ email_id: emailId, to_category: toCategory }),
    }),

  bulk: (payload: {
    action: BulkActionType;
    email_ids?: number[];
    category?: string;
    value?: string;
    dry_run?: boolean;
  }) =>
    request<BulkActionResult>("/actions/bulk", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  sync: (opts: { limit?: number; reset?: boolean } = {}) =>
    request<{ source: string; added: number; reset: boolean }>(
      `/sync${qs({ limit: opts.limit, reset: opts.reset })}`,
      { method: "POST" },
    ),

  recategorize: () => request<{ recategorized: number }>("/recategorize", { method: "POST" }),

  automations: () => request<Automation[]>("/automations"),
  createAutomation: (payload: Omit<Automation, "id" | "run_count" | "created_at">) =>
    request<Automation>("/automations", { method: "POST", body: JSON.stringify(payload) }),
  deleteAutomation: (id: number) => request(`/automations/${id}`, { method: "DELETE" }),
  runAutomations: (dryRun: boolean) =>
    request<AutomationRunResult>(`/automations/run${qs({ dry_run: dryRun })}`, { method: "POST" }),
};

export type { Email };
