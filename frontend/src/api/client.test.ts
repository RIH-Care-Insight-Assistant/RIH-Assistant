import { afterEach, describe, expect, it, vi } from "vitest";
import { api, ApiError, resetClientStateForTests } from "./client";

afterEach(() => resetClientStateForTests());

function respond(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

describe("api client retries", () => {
  it("retries an idempotent read once after a 503", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(respond(503, { error: { code: "dependency_unavailable", message: "x", request_id: "r" } }))
      .mockResolvedValueOnce(respond(200, { items: [] }));
    vi.stubGlobal("fetch", fetchMock);
    await expect(api.listSessions()).resolves.toEqual({ items: [] });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("gives up after one retry", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      respond(503, { error: { code: "dependency_unavailable", message: "x", request_id: "r" } }));
    vi.stubGlobal("fetch", fetchMock);
    await expect(api.listSessions()).rejects.toBeInstanceOf(ApiError);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("never retries a write such as a chat turn", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(respond(200, { csrf_token: "csrf-test-token-0123456789" }))
      .mockResolvedValue(respond(503, { error: { code: "dependency_unavailable", message: "x", request_id: "r" } }));
    vi.stubGlobal("fetch", fetchMock);
    await expect(api.chat("ses_1", "hello")).rejects.toMatchObject({ status: 503 });
    expect(fetchMock.mock.calls.filter((c) => String(c[0]).endsWith("/chat"))).toHaveLength(1);
  });

  it("does not retry client errors", async () => {
    const fetchMock = vi.fn().mockResolvedValue(respond(404, { error: { code: "not_found", message: "x", request_id: "r" } }));
    vi.stubGlobal("fetch", fetchMock);
    await expect(api.messages("ses_x")).rejects.toMatchObject({ status: 404 });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
