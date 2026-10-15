import type { Session } from "../api/types";
import { Icon } from "./Icon";

interface Props {
  sessions: Session[];
  current: string | null;
  onOpen: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}

function when(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}

export function SessionList({ sessions, current, onOpen, onNew, onDelete }: Props) {
  return (
    <nav className="sessions" aria-label="Conversation history">
      <button type="button" className="btn btn--primary sessions__new" onClick={onNew}>
        <Icon name="plus" />
        New conversation
      </button>
      <p className="sessions__heading">
        <span>Recent</span>
        {sessions.length > 0 && <span className="sessions__count">{sessions.length}</span>}
      </p>
      {sessions.length === 0 ? (
        <div className="sessions__empty">
          <Icon name="chat" />
          <p>No saved conversations yet.</p>
        </div>
      ) : (
        <ul className="sessions__list">
          {sessions.map((s) => (
            <li key={s.id} className={s.id === current ? "sessions__item is-current" : "sessions__item"}>
              <button
                type="button"
                className="sessions__open"
                aria-current={s.id === current ? "true" : undefined}
                onClick={() => onOpen(s.id)}
              >
                <span className="sessions__title">{s.title || "New conversation"}</span>
                {/* Decorative: the button's accessible name stays the conversation title. */}
                <span className="sessions__time" aria-hidden="true">
                  {when(s.updated_at)}
                </span>
              </button>
              <button
                type="button"
                className="btn btn--icon"
                aria-label={`Delete conversation: ${s.title || "New conversation"}`}
                title="Delete conversation"
                onClick={() => onDelete(s.id)}
              >
                <Icon name="trash" />
              </button>
            </li>
          ))}
        </ul>
      )}
      <p className="sessions__note">
        <Icon name="clock" />
        <span>Conversations are kept for 24 hours on this device's session.</span>
      </p>
    </nav>
  );
}
