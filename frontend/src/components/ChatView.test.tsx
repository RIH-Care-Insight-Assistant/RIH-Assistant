import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { resetClientStateForTests } from "../api/client";
import { installFakeApi, makeMessage } from "../test/fakeApi";
import { ChatView } from "./ChatView";

const CRISIS =
  "If you might be in danger or considering self-harm: Call 911, or call or text 988, now. (synthetic test copy)";

beforeEach(() => resetClientStateForTests());

describe("ChatView", () => {
  it("shows an empty state with example questions", async () => {
    installFakeApi();
    render(<ChatView />);
    expect(screen.getByRole("heading", { name: /how can i help/i })).toBeInTheDocument();
    expect(screen.getByRole("list", { name: /example questions/i })).toBeInTheDocument();
    expect(await screen.findByText(/no saved conversations/i)).toBeInTheDocument();
  });

  it("creates a session on first send, shows the reply with citations, and sends CSRF", async () => {
    const api = installFakeApi({
      nextChat: () => ({
        message: makeMessage({
          role: "assistant",
          text: "Here's what I found:\n[1] RIH Hours & Location: Open weekdays.",
          citations: [
            {
              source_id: "src_1", chunk_id: "chk_1", title: "RIH Hours & Location", url: "https://health.umbc.edu/",
              version: "abc123", approval_status: "baseline", approved_at: null, checked_at: null, freshness: "stale",
            },
          ],
        }),
        notices: [{ kind: "stale_source", message: "Some sources were last updated over a year ago." }],
      }),
    });
    const user = userEvent.setup();
    render(<ChatView />);
    await user.type(screen.getByLabelText(/your message/i), "What are the RIH hours?");
    await user.click(screen.getByRole("button", { name: "Send" }));

    const sources = await screen.findByRole("region", { name: "Sources" });
    const link = within(sources).getByRole("link", { name: "RIH Hours & Location" });
    expect(link).toHaveAttribute("href", "https://health.umbc.edu/");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
    expect(within(sources).getByText(/awaiting governed review/i)).toBeInTheDocument();
    expect(screen.getByText(/last updated over a year ago/i)).toBeInTheDocument();
    expect(screen.getAllByText("What are the RIH hours?").length).toBeGreaterThan(0);

    const posts = api.calls.filter((c) => c.method === "POST");
    expect(posts.map((c) => c.path)).toEqual(["/api/v1/sessions", "/api/v1/chat"]);
    for (const c of posts) expect(c.headers["X-CSRF-Token"]).toBe("csrf-test-token-0123456789");
  });

  it("renders safety guidance as a distinct alert without citations or feedback suppression", async () => {
    installFakeApi({
      nextChat: () => ({
        response_type: "safety",
        safety_lane: "urgent_safety",
        is_terminal_safety: true,
        message: makeMessage({ role: "assistant", text: CRISIS, response_type: "safety", safety_lane: "urgent_safety" }),
      }),
    });
    const user = userEvent.setup();
    render(<ChatView />);
    await user.type(screen.getByLabelText(/your message/i), "synthetic crisis test message");
    await user.click(screen.getByRole("button", { name: "Send" }));
    const alert = await screen.findByRole("alert");
    expect(within(alert).getByRole("heading", { name: /urgent safety guidance/i })).toBeInTheDocument();
    expect(within(alert).getByText(CRISIS)).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Sources" })).not.toBeInTheDocument();
  });

  it("offers server-defined clarification options and sends the option id", async () => {
    let n = 0;
    const api = installFakeApi({
      nextChat: () =>
        ++n === 1
          ? {
              response_type: "clarification",
              clarification: {
                prompt: "Do you mean a counseling appointment or a medical appointment?",
                options: [
                  { id: "counseling_appointment", label: "Counseling appointment" },
                  { id: "medical_appointment", label: "Medical appointment" },
                ],
              },
              message: makeMessage({
                role: "assistant",
                text: "Do you mean a counseling appointment or a medical appointment?",
                response_type: "clarification",
                clarification: {
                  prompt: "Do you mean a counseling appointment or a medical appointment?",
                  options: [
                    { id: "counseling_appointment", label: "Counseling appointment" },
                    { id: "medical_appointment", label: "Medical appointment" },
                  ],
                },
              }),
            }
          : {},
    });
    const user = userEvent.setup();
    render(<ChatView />);
    await user.type(screen.getByLabelText(/your message/i), "I need an appointment");
    await user.click(screen.getByRole("button", { name: "Send" }));
    await user.click(await screen.findByRole("button", { name: "Medical appointment" }));
    await waitFor(() => expect(api.calls.filter((c) => c.path === "/api/v1/chat")).toHaveLength(2));
    const second = api.calls.filter((c) => c.path === "/api/v1/chat")[1];
    expect(second.body).toEqual({ session_id: expect.any(String), clarification_option_id: "medical_appointment" });
  });

  it("records feedback with aria-pressed state", async () => {
    const api = installFakeApi();
    const user = userEvent.setup();
    render(<ChatView />);
    await user.type(screen.getByLabelText(/your message/i), "hours?");
    await user.click(screen.getByRole("button", { name: "Send" }));
    const helpful = await screen.findByRole("button", { name: "Helpful" });
    expect(helpful).toHaveAttribute("aria-pressed", "false");
    await user.click(helpful);
    await waitFor(() => expect(helpful).toHaveAttribute("aria-pressed", "true"));
    expect(api.calls.some((c) => c.path === "/api/v1/feedback" && (c.body as { rating: string }).rating === "helpful")).toBe(true);
  });

  it("shows a friendly error with the request reference when the service is unavailable", async () => {
    installFakeApi({ nextChat: () => ({ status: 503, error: "dependency_unavailable" }) });
    const user = userEvent.setup();
    render(<ChatView />);
    await user.type(screen.getByLabelText(/your message/i), "hours?");
    await user.click(screen.getByRole("button", { name: "Send" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/temporarily unavailable/i);
    expect(screen.getByLabelText(/your message/i)).toHaveValue("hours?"); // draft kept for retry
  });

  it("renders message text as text, never as HTML", async () => {
    installFakeApi({
      nextChat: () => ({ message: makeMessage({ role: "assistant", text: "<img src=x onerror=alert(1)><b>bold</b>" }) }),
    });
    const user = userEvent.setup();
    const { container } = render(<ChatView />);
    await user.type(screen.getByLabelText(/your message/i), "x");
    await user.click(screen.getByRole("button", { name: "Send" }));
    expect(await screen.findByText("<img src=x onerror=alert(1)><b>bold</b>")).toBeInTheDocument();
    expect(container.querySelector("img")).toBeNull();
    expect(container.querySelector("b")).toBeNull();
  });

  it("loads and deletes saved conversations", async () => {
    const api = installFakeApi({
      sessions: [{ id: "ses_saved", title: "Earlier question", created_at: "x", updated_at: "x" }],
      messages: {
        ses_saved: [
          makeMessage({ role: "user", text: "Earlier question", session_id: "ses_saved" }),
          makeMessage({ role: "assistant", text: "Earlier answer", session_id: "ses_saved" }),
        ],
      },
    });
    const user = userEvent.setup();
    render(<ChatView />);
    await user.click(await screen.findByRole("button", { name: "Earlier question" }));
    expect(await screen.findByText("Earlier answer")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /delete conversation: earlier question/i }));
    await waitFor(() => expect(api.calls.some((c) => c.method === "DELETE")).toBe(true));
    expect(await screen.findByText(/no saved conversations/i)).toBeInTheDocument();
  });
});
