// In-memory fake of the /api/v1 contract for component tests (no network, synthetic data).
import { vi } from "vitest";
import type { ChatResponse, Message, Readiness, RiskItem, Session, SourceRow } from "../api/types";

export interface FakeState {
  sessions: Session[];
  messages: Record<string, Message[]>;
  calls: { method: string; path: string; body: unknown; headers: Record<string, string> }[];
  nextChat?: (body: Record<string, unknown>) => Partial<ChatResponse> | { status: number; error: string };
  staff?: { username: string; roles: string[] };
  sources?: SourceRow[];
  risks?: RiskItem[];
  readiness?: Readiness;
  reviews: { path: string; body: unknown }[];
}

let counter = 0;
const id = (p: string) => `${p}_${++counter}`;
const now = () => "2026-10-14T12:00:00Z";

export function makeMessage(over: Partial<Message> & { role: Message["role"]; text: string }): Message {
  return {
    id: id("msg"),
    session_id: "ses_1",
    created_at: now(),
    citations: [],
    safety_lane: null,
    response_type: over.role === "assistant" ? "answer" : null,
    clarification: null,
    ...over,
  };
}

function json(status: number, body: unknown): Response {
  return new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

export function installFakeApi(state: Partial<FakeState> = {}): FakeState {
  const s: FakeState = { sessions: [], messages: {}, calls: [], reviews: [], ...state };
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input), "http://localhost");
    const method = (init?.method ?? "GET").toUpperCase();
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    const headers = (init?.headers ?? {}) as Record<string, string>;
    s.calls.push({ method, path: url.pathname + url.search, body, headers });
    const p = url.pathname.replace("/api/v1", "");

    if (p === "/csrf") return json(200, { csrf_token: "csrf-test-token-0123456789" });
    if (method !== "GET" && headers["X-CSRF-Token"] !== "csrf-test-token-0123456789") {
      return json(403, { error: { code: "forbidden", message: "This action is not allowed.", request_id: "r1" } });
    }
    if (p === "/sessions" && method === "GET") return json(200, { items: s.sessions });
    if (p === "/sessions" && method === "POST") {
      const ses: Session = { id: id("ses"), title: null, created_at: now(), updated_at: now() };
      s.sessions.unshift(ses);
      s.messages[ses.id] = [];
      return json(201, ses);
    }
    const msgMatch = p.match(/^\/sessions\/([^/]+)\/messages$/);
    if (msgMatch) return json(200, { items: s.messages[msgMatch[1]] ?? [], next_cursor: null });
    const delMatch = p.match(/^\/sessions\/([^/]+)$/);
    if (delMatch && method === "DELETE") {
      s.sessions = s.sessions.filter((x) => x.id !== delMatch[1]);
      return new Response(null, { status: 204 });
    }
    if (p === "/chat") {
      const b = body as Record<string, unknown>;
      const custom = s.nextChat?.(b);
      if (custom && "status" in custom && "error" in custom) {
        return json(custom.status, { error: { code: custom.error, message: "Request failed.", request_id: "req-42" } });
      }
      const sid = String(b.session_id);
      const user = makeMessage({ role: "user", text: String(b.message ?? "chosen option"), session_id: sid });
      const assistant = makeMessage({ role: "assistant", text: "Here's what I found:", session_id: sid });
      const res: ChatResponse = {
        session_id: sid,
        user_message: user,
        message: assistant,
        response_type: "answer",
        safety_lane: null,
        is_terminal_safety: false,
        citations: [],
        clarification: null,
        notices: [],
        persisted: true,
        ...(custom as Partial<ChatResponse>),
      };
      if (custom && "message" in custom && custom.message) res.message = { ...assistant, ...custom.message };
      s.messages[sid] = [...(s.messages[sid] ?? []), res.user_message, res.message];
      const ses = s.sessions.find((x) => x.id === sid);
      if (ses && !ses.title) ses.title = user.text.slice(0, 40);
      return json(200, res);
    }
    if (p === "/feedback") return json(201, { id: "fbk_1", created_at: now(), ...(body as object) });
    if (p.startsWith("/resources")) {
      return json(200, {
        items: [
          {
            id: "chk_1",
            title: "RIH Hours & Location",
            url: "https://health.umbc.edu/",
            category: "hours",
            provenance: {
              source_id: "src_1", version: "abc123", content_sha256: "f".repeat(64), updated_on: "2025-10-04",
              approval_status: "baseline", approved_at: null, approved_by: null, checked_at: null,
              expires_at: null, freshness: "stale",
            },
          },
        ],
      });
    }
    if (p === "/auth/me") return json(200, s.staff ? { authenticated: true, user: s.staff } : { authenticated: false, user: null });
    if (p === "/auth/login") {
      const b = body as { username: string; password: string };
      if (b.password !== "synthetic-Test-pass-0001") {
        return json(401, { error: { code: "unauthenticated", message: "x", request_id: "r" } });
      }
      s.staff = { username: b.username, roles: b.username.startsWith("adam") ? ["admin"] : ["reviewer"] };
      return json(200, { authenticated: true, user: s.staff });
    }
    if (p === "/auth/logout") {
      s.staff = undefined;
      return new Response(null, { status: 204 });
    }
    if (p === "/admin/sources" && s.staff) return json(200, { items: s.sources ?? [] });
    if (p.startsWith("/admin/sources/") && s.staff) {
      s.reviews.push({ path: p, body });
      return json(200, { status: (body as { status: string }).status });
    }
    if (p === "/admin/users" && s.staff?.roles.includes("admin")) return json(200, { items: [] });
    if (p === "/admin/governance/risks" && s.staff) {
      return json(200, { register_version: "risks-1", framework: "Aligned with NIST AI RMF.", status_note: "Agent-proposed.",
        integrity_problems: [], items: s.risks ?? [] });
    }
    if (p === "/admin/governance/readiness" && s.staff) {
      return json(200, s.readiness ?? { status: "not_ready", register_version: "risks-1", candidate: null,
        blockers: ["release battery evidence is missing"], pending_human_decisions: [], redteam: null, checks: [],
        evidence_generated_at: null, snapshot_sha256: "a".repeat(64) });
    }
    if (p.startsWith("/admin/governance/") && method === "POST" && s.staff) {
      s.reviews.push({ path: p, body });
      if (p.endsWith("release-decisions") && !s.staff.roles.includes("admin")) {
        return json(403, { error: { code: "forbidden", message: "x", request_id: "r" } });
      }
      return json(201, { ok: true });
    }
    if (p.startsWith("/admin")) {
      return s.staff
        ? json(403, { error: { code: "forbidden", message: "x", request_id: "r" } })
        : json(401, { error: { code: "unauthenticated", message: "x", request_id: "r" } });
    }
    return json(404, { error: { code: "not_found", message: "Not found.", request_id: "r" } });
  });
  vi.stubGlobal("fetch", fetchMock);
  return s;
}
