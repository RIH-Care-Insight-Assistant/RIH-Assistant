import type { Session } from "../api/types";

interface Props {
  sessions: Session[];
  current: string | null;
  onOpen: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}

export function SessionList({ sessions, current, onOpen, onNew, onDelete }: Props) {
  return (
    <nav className="sessions" aria-label="Conversation history">
      <button type="button" className="btn btn--primary sessions__new" onClick={onNew}>
        New conversation
      </button>
      {sessions.length === 0 ? (
        <p className="sessions__empty">No saved conversations yet.</p>
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
                {s.title || "New conversation"}
              </button>
              <button
                type="button"
                className="btn btn--icon"
                aria-label={`Delete conversation: ${s.title || "New conversation"}`}
                onClick={() => onDelete(s.id)}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
      <p className="sessions__note">Conversations are kept for 24 hours on this device's session.</p>
    </nav>
  );
}
