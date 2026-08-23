/**
 * Thin typed wrapper around the SpendLens backend.
 *
 * In dev, requests go through Next's rewrites (configured in next.config.mjs)
 * to NEXT_PUBLIC_API_URL. That avoids any CORS surprises and lets the frontend
 * call `/api/...` from the browser.
 */

const BASE = "/api";

export type Category = {
  id: number;
  name: string;
  color: string;
  icon: string;
};

export type Transaction = {
  id: number;
  occurred_on: string;
  description: string;
  amount: string;
  currency: string;
  merchant: string | null;
  category: Category | null;
  created_at: string;
};

export type Totals = {
  income: string;
  expense: string;
  net: string;
  transaction_count: number;
};

export type CategoryBreakdown = {
  category: string;
  color: string;
  icon: string;
  total: string;
  share: number;
  transaction_count: number;
};

export type TimeseriesPoint = {
  bucket: string;
  income: string;
  expense: string;
};

export type Insight = {
  kind: string;
  title: string;
  body: string;
  value: string | null;
};

export type Statement = {
  id: number;
  filename: string;
  file_type: string;
  row_count: number;
  uploaded_at: string;
};

export type UploadResult = {
  statement: Statement;
  imported: number;
  categorized: number;
  skipped: number;
};

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers || {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* swallow */
    }
    throw new Error(detail || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

function qs(params: Record<string, string | number | undefined | null>): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "");
  if (entries.length === 0) return "";
  const usp = new URLSearchParams();
  for (const [k, v] of entries) usp.set(k, String(v));
  return `?${usp.toString()}`;
}

export const api = {
  categories: () => request<Category[]>("/categories"),

  transactions: (params: {
    start?: string;
    end?: string;
    category_id?: number;
    q?: string;
    limit?: number;
    offset?: number;
  } = {}) => request<Transaction[]>(`/transactions${qs(params)}`),

  updateTransaction: (id: number, body: Partial<Pick<Transaction, "description" | "merchant" | "amount">> & { category_id?: number }) =>
    request<Transaction>(`/transactions/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  deleteTransaction: (id: number) =>
    request<void>(`/transactions/${id}`, { method: "DELETE" }),

  totals: (params: { start?: string; end?: string } = {}) =>
    request<Totals>(`/analytics/totals${qs(params)}`),

  categoryBreakdown: (params: { start?: string; end?: string } = {}) =>
    request<CategoryBreakdown[]>(`/analytics/categories${qs(params)}`),

  timeseries: (params: { bucket?: "day" | "month"; start?: string; end?: string } = {}) =>
    request<TimeseriesPoint[]>(`/analytics/timeseries${qs(params)}`),

  insights: (params: { start?: string; end?: string } = {}) =>
    request<Insight[]>(`/analytics/insights${qs(params)}`),

  statements: () => request<Statement[]>("/statements"),

  uploadStatement: async (file: File): Promise<UploadResult> => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${BASE}/statements/upload`, {
      method: "POST",
      body: form,
    });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = await res.json();
        detail = body.detail ?? detail;
      } catch {
        /* swallow */
      }
      throw new Error(detail);
    }
    return res.json();
  },

  deleteStatement: (id: number) =>
    request<void>(`/statements/${id}`, { method: "DELETE" }),
};
