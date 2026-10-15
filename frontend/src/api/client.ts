// Typed API client. Centralizes credentials (same-origin cookies), the CSRF header and
// error handling; components never call fetch directly.

import type {
  AuditEvent,
  ChatResponse,
  ErrorBody,
  Feedback,
  Me,
  MessagePage,
  Rating,
  Readiness,
  Resource,
  RiskItem,
  Session,
  SourceRow,
  UserRow,
} from "./types";

const BASE = "/api/v1";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId: string;

  constructor(status: number, body: ErrorBody | null) {
    super(body?.message ?? "The service could not be reached.");
    this.status = status;
    this.code = body?.code ?? (status === 0 ? "network_error" : "internal_error");
    this.requestId = body?.request_id ?? "";
  }
}

let csrfToken: string | null = null;

async function ensureCsrf(): Promise<string> {
  if (csrfToken) return csrfToken;
  const res = await fetch(`${BASE}/csrf`, { credentials: "same-origin" });
  if (!res.ok) throw new ApiError(res.status, null);
  csrfToken = ((await res.json()) as { csrf_token: string }).csrf_token;
  return csrfToken;
}

async function request<T>(method: string, path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (method !== "GET") {
    headers["Content-Type"] = "application/json";
    headers["X-CSRF-Token"] = await ensureCsrf();
  }
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      headers,
      credentials: "same-origin",
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    });
  } catch (err) {
    if ((err as Error).name === "AbortError") throw err;
    throw new ApiError(0, null);
  }
  if (res.status === 204) return undefined as T;
  let data: unknown = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }
  if (!res.ok) {
    const envelope = data as { error?: ErrorBody } | null;
    if (res.status === 403 && envelope?.error?.code === "forbidden") csrfToken = null;
    throw new ApiError(res.status, envelope?.error ?? null);
  }
  return data as T;
}

export const api = {
  createSession: () => request<Session>("POST", "/sessions", {}),
  listSessions: () => request<{ items: Session[] }>("GET", "/sessions"),
  deleteSession: (id: string) => request<void>("DELETE", `/sessions/${encodeURIComponent(id)}`),
  messages: (id: string, cursor?: string | null) =>
    request<MessagePage>(
      "GET",
      `/sessions/${encodeURIComponent(id)}/messages?limit=50${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ""}`,
    ),
  chat: (sessionId: string, message: string, signal?: AbortSignal) =>
    request<ChatResponse>("POST", "/chat", { session_id: sessionId, message }, signal),
  chooseOption: (sessionId: string, optionId: string) =>
    request<ChatResponse>("POST", "/chat", { session_id: sessionId, clarification_option_id: optionId }),
  feedback: (sessionId: string, messageId: string, rating: Rating) =>
    request<Feedback>("POST", "/feedback", { session_id: sessionId, message_id: messageId, rating }),
  resources: (q: string, signal?: AbortSignal) =>
    request<{ items: Resource[] }>("GET", `/resources?limit=20${q ? `&q=${encodeURIComponent(q)}` : ""}`, undefined, signal),
};

export const staffApi = {
  me: () => request<Me>("GET", "/auth/me"),
  login: (username: string, password: string) => request<Me>("POST", "/auth/login", { username, password }),
  logout: () => request<void>("POST", "/auth/logout", {}),
  status: () => request<{ policy_version: string; policy_sha256: string }>("GET", "/admin/status"),
  sources: () => request<{ items: SourceRow[] }>("GET", "/admin/sources"),
  review: (chunkId: string, status: string, note: string) =>
    request<{ status: string }>("POST", `/admin/sources/${encodeURIComponent(chunkId)}/review`, { status, note }),
  feedbackSummary: () => request<{ helpful: number; not_helpful: number }>("GET", "/admin/feedback/summary"),
  users: () => request<{ items: UserRow[] }>("GET", "/admin/users"),
  createUser: (username: string, password: string, roles: string[]) =>
    request<UserRow>("POST", "/admin/users", { username, password, roles }),
  disableUser: (id: string) => request<{ disabled: boolean }>("POST", `/admin/users/${encodeURIComponent(id)}/disable`, {}),
  audit: (limit = 100) => request<{ items: AuditEvent[] }>("GET", `/admin/audit?limit=${limit}`),
  risks: () => request<{ register_version: string; framework: string; status_note: string; integrity_problems: string[]; items: RiskItem[] }>("GET", "/admin/governance/risks"),
  readiness: () => request<Readiness>("GET", "/admin/governance/readiness"),
  reviewRisk: (riskId: string, decision: string, rationale: string) =>
    request<unknown>("POST", `/admin/governance/risks/${encodeURIComponent(riskId)}/reviews`, { decision, rationale }),
  releaseDecision: (decision: string, rationale: string, snapshot: string) =>
    request<unknown>("POST", "/admin/governance/release-decisions", { decision, rationale, snapshot_sha256: snapshot }),
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  observability: () => request<any>("GET", "/admin/observability/summary?spans=40"),
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  incidents: () => request<any>("GET", "/admin/incidents"),
  simulateIncident: (scenario: string) =>
    request<{ outcome: string; detected_by: string[] }>("POST", "/admin/incidents/simulate", { scenario }),
  ingest: (url: string, category: string) =>
    request<{ chunk_id: string; status: string; signals: string[] }>("POST", "/admin/ingest", { url, category }),
};

/** Only absolute HTTPS URLs become links; anything else is shown as plain text. */
export function safeHttpsUrl(raw: string): string | null {
  try {
    const u = new URL(raw);
    return u.protocol === "https:" && !u.username && !u.password ? u.toString() : null;
  } catch {
    return null;
  }
}

export function resetClientStateForTests(): void {
  csrfToken = null;
}
