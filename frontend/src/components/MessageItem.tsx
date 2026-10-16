import type { Message, Notice, Rating } from "../api/types";
import { Citations } from "./Citations";
import { Icon } from "./Icon";

const LANE_TITLE: Record<string, string> = {
  urgent_safety: "Urgent safety guidance",
  title_ix: "Title IX support",
  harassment_hate: "Student Conduct and CARE support",
};

interface Props {
  message: Message;
  notices?: Notice[];
  rating?: Rating;
  onRate?: (rating: Rating) => void;
  onChoose?: (optionId: string) => void;
  optionsDisabled?: boolean;
}

export function MessageItem({ message, notices = [], rating, onRate, onChoose, optionsDisabled }: Props) {
  if (message.role === "user") {
    return (
      <li className="msg msg--user">
        <span className="visually-hidden">You said: </span>
        <p className="msg__text">{message.text}</p>
      </li>
    );
  }
  const safety = message.response_type === "safety" && message.safety_lane;
  return (
    <li className={`msg msg--assistant${safety ? " msg--safety" : ""}`}>
      <span className="avatar" aria-hidden="true">
        <Icon name={safety ? "alert" : "compass"} />
      </span>
      <div className="msg__bubble">
        {safety ? (
          <div role="alert" className="safety-panel">
            <h3 className="safety-panel__title">
              <Icon name="shield" />
              {LANE_TITLE[message.safety_lane as string]}
            </h3>
            <p className="msg__text">{message.text}</p>
          </div>
        ) : (
          <>
            <span className="msg__meta" aria-hidden="true">
              Care Insight Assistant
            </span>
            <span className="visually-hidden">Assistant said: </span>
            <p className="msg__text">{message.text}</p>
          </>
        )}
        {notices.length > 0 && (
          <ul className="notices" aria-label="Notices about this answer">
            {notices.map((n) => (
              <li key={n.kind} className={`notice notice--${n.kind}`}>
                <Icon name="info" />
                <span>{n.message}</span>
              </li>
            ))}
          </ul>
        )}
        {message.clarification && onChoose && (
          <fieldset className="clarify" disabled={optionsDisabled}>
            <legend>{message.clarification.prompt}</legend>
            {message.clarification.options.map((o) => (
              <button key={o.id} type="button" className="btn btn--secondary" onClick={() => onChoose(o.id)}>
                {o.label}
              </button>
            ))}
          </fieldset>
        )}
        <Citations citations={message.citations} />
        {onRate && !message.id.startsWith("tmp_") && (
          <div className="feedback" role="group" aria-label="Was this helpful?">
            <span className="feedback__label">Was this helpful?</span>
            <button
              type="button"
              className="btn btn--small"
              aria-pressed={rating === "helpful"}
              onClick={() => onRate("helpful")}
            >
              <Icon name="thumbUp" />
              Helpful
            </button>
            <button
              type="button"
              className="btn btn--small"
              aria-pressed={rating === "not_helpful"}
              onClick={() => onRate("not_helpful")}
            >
              <Icon name="thumbUp" flip />
              Not helpful
            </button>
          </div>
        )}
      </div>
    </li>
  );
}
