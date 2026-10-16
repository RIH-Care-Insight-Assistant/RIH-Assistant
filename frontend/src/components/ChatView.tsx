import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api/client";
import type { ChatResponse, Message, Notice, Rating, Session } from "../api/types";
import { Icon, type IconName } from "./Icon";
import { MessageItem } from "./MessageItem";
import { SessionList } from "./SessionList";

const MAX_CHARS = 4000;
const SUGGESTIONS: { text: string; icon: IconName }[] = [
  { text: "What are the RIH hours?", icon: "clock" },
  { text: "How do I submit immunization records?", icon: "clipboard" },
  { text: "I need an appointment", icon: "calendar" },
];

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
      <section className="chat" aria-label="Conversation">
        <div className="chat__header">
          <div className="chat__title">
            <span className="avatar" aria-hidden="true">
              <Icon name="compass" />
            </span>
            <div>
              <h2>Campus resource assistant</h2>
              <p>Answers come from approved sources, with citations.</p>
            </div>
          </div>
          <div className="chat__badges">
            <span className="pill pill--good">Safety checks first</span>
            <span className="pill">Synthetic demo</span>
          </div>
        </div>
        <div className="chat__body">
          {error && (
            <div className="error-banner" role="alert">
              <Icon name="alert" />
              <span>{error}</span>
            </div>
          )}
          {loadingHistory ? (
            <p className="loading" role="status">
              <span className="spinner" aria-hidden="true" />
              Loading conversation…
            </p>
          ) : messages.length === 0 ? (
            <div className="welcome">
              <span className="welcome__mark" aria-hidden="true">
                <Icon name="compass" />
              </span>
              <h2>How can I help you find campus resources?</h2>
              <p>Ask about RIH hours, appointments, billing, immunizations or counseling services.</p>
              <ul className="suggestions" aria-label="Example questions">
                {SUGGESTIONS.map((s) => (
                  <li key={s.text}>
                    <button type="button" className="suggestion" onClick={() => void send(s.text)} disabled={busy}>
                      <span className="suggestion__icon" aria-hidden="true">
                        <Icon name={s.icon} />
                      </span>
                      {s.text}
                    </button>
                  </li>
                ))}
              </ul>
              <p className="welcome__safety">
                <Icon name="shieldCheck" />
                <span>
                  Messages about a crisis, sexual misconduct or threats are checked first and get fixed safety guidance
                  straight away.
                </span>
              </p>
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
            <p className="typing" role="status">
              <span className="typing__dots" aria-hidden="true">
                <span />
                <span />
                <span />
              </span>
              The assistant is responding…
            </p>
          )}
        </div>
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
          <div className="composer__box">
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
                <Icon name="send" />
                Send
              </button>
            </div>
          </div>
        </form>
      </section>
      <SessionList sessions={sessions} current={current} onOpen={openSession} onNew={newChat} onDelete={remove} />
    </div>
  );
}
