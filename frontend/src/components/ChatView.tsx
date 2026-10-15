import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api/client";
import type { ChatResponse, Message, Notice, Rating, Session } from "../api/types";
import { MessageItem } from "./MessageItem";
import { SessionList } from "./SessionList";

const MAX_CHARS = 4000;
const SUGGESTIONS = ["What are the RIH hours?", "How do I submit immunization records?", "I need an appointment"];

function describe(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.code === "rate_limited") return "You're sending messages quickly. Please wait a moment and try again.";
    if (err.code === "dependency_unavailable") return "The assistant is temporarily unavailable. Please try again shortly.";
    if (err.code === "network_error") return "Can't reach the assistant. Check your connection and try again.";
    return `${err.message}${err.requestId ? ` (reference ${err.requestId})` : ""}`;
  }
  return "Something went wrong.";
}

export function ChatView() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [current, setCurrent] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [notices, setNotices] = useState<Record<string, Notice[]>>({});
  const [ratings, setRatings] = useState<Record<string, Rating>>({});
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLLIElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const refreshSessions = useCallback(async () => {
    try {
      setSessions((await api.listSessions()).items);
    } catch (err) {
      if (!(err instanceof ApiError && err.code === "unauthenticated")) setError(describe(err));
      setSessions([]);
    }
  }, []);

  useEffect(() => {
    let active = true;
    api
      .listSessions()
      .then((r) => active && setSessions(r.items))
      .catch(() => active && setSessions([])); // no credential yet: nothing saved
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ block: "end" });
  }, [messages]);

  const openSession = async (id: string) => {
    setCurrent(id);
    setError(null);
    setLoadingHistory(true);
    setNotices({});
    try {
      setMessages((await api.messages(id)).items);
    } catch (err) {
      setError(describe(err));
      setMessages([]);
    } finally {
      setLoadingHistory(false);
    }
  };

  const newChat = () => {
    setCurrent(null);
    setMessages([]);
    setNotices({});
    setError(null);
    inputRef.current?.focus();
  };

  const ensureSession = async (): Promise<string> => {
    if (current) return current;
    const s = await api.createSession();
    setCurrent(s.id);
    return s.id;
  };

  const applyResponse = (res: ChatResponse) => {
    setMessages((prev) => [...prev, res.user_message, res.message]);
    if (res.notices.length) setNotices((prev) => ({ ...prev, [res.message.id]: res.notices }));
    void refreshSessions();
  };

  const send = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      applyResponse(await api.chat(sid, trimmed));
      setDraft("");
    } catch (err) {
      setError(describe(err));
    } finally {
      setBusy(false);
      inputRef.current?.focus();
    }
  };

  const choose = async (optionId: string) => {
    if (!current || busy) return;
    setBusy(true);
    setError(null);
    try {
      applyResponse(await api.chooseOption(current, optionId));
    } catch (err) {
      setError(describe(err));
    } finally {
      setBusy(false);
    }
  };

  const rate = async (messageId: string, rating: Rating) => {
    if (!current) return;
    try {
      await api.feedback(current, messageId, rating);
      setRatings((prev) => ({ ...prev, [messageId]: rating }));
    } catch (err) {
      setError(describe(err));
    }
  };

  const remove = async (id: string) => {
    try {
      await api.deleteSession(id);
      if (id === current) newChat();
      await refreshSessions();
    } catch (err) {
      setError(describe(err));
    }
  };

  const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");

  return (
    <div className="chat-layout">
      <SessionList sessions={sessions} current={current} onOpen={openSession} onNew={newChat} onDelete={remove} />
      <section className="chat" aria-label="Conversation">
        {error && (
          <div className="error-banner" role="alert">
            {error}
          </div>
        )}
        {loadingHistory ? (
          <p className="empty">Loading conversation…</p>
        ) : messages.length === 0 ? (
          <div className="empty">
            <h2>How can I help you find campus resources?</h2>
            <p>Ask about RIH hours, appointments, billing, immunizations or counseling services.</p>
            <ul className="suggestions" aria-label="Example questions">
              {SUGGESTIONS.map((s) => (
                <li key={s}>
                  <button type="button" className="btn btn--chip" onClick={() => void send(s)} disabled={busy}>
                    {s}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <ol className="transcript" aria-live="polite" aria-relevant="additions">
            {messages.map((m) => (
              <MessageItem
                key={m.id}
                message={m}
                notices={notices[m.id]}
                rating={ratings[m.id]}
                onRate={m.role === "assistant" ? (r) => void rate(m.id, r) : undefined}
                onChoose={m === lastAssistant ? (id) => void choose(id) : undefined}
                optionsDisabled={busy}
              />
            ))}
            <li ref={endRef} aria-hidden="true" className="transcript__end" />
          </ol>
        )}
        {busy && (
          <p className="status" role="status">
            The assistant is responding…
          </p>
        )}
        <form
          className="composer"
          onSubmit={(e) => {
            e.preventDefault();
            void send(draft);
          }}
        >
          <label htmlFor="composer-input" className="composer__label">
            Your message
          </label>
          <textarea
            id="composer-input"
            ref={inputRef}
            value={draft}
            maxLength={MAX_CHARS}
            rows={2}
            placeholder="Ask about campus health resources…"
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void send(draft);
              }
            }}
            aria-describedby="composer-hint"
          />
          <div className="composer__row">
            <span id="composer-hint" className="composer__hint">
              {draft.length}/{MAX_CHARS} · Enter to send, Shift+Enter for a new line
            </span>
            <button type="submit" className="btn btn--primary" disabled={busy || !draft.trim()}>
              Send
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
