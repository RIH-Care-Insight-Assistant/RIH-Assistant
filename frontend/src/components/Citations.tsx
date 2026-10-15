import type { Citation } from "../api/types";
import { safeHttpsUrl } from "../api/client";

const APPROVAL_LABEL: Record<string, string> = {
  approved: "Approved source",
  baseline: "Baseline source, awaiting governed review",
  pending: "Pending review",
  rejected: "Rejected",
  retired: "Retired",
};

const FRESHNESS_LABEL: Record<string, string> = {
  fresh: "Recently updated",
  aging: "Updated over 6 months ago",
  stale: "Updated over a year ago; check the official page",
  expired: "Out of date",
  unknown: "Update date unknown",
};

export function Citations({ citations }: { citations: Citation[] }) {
  if (citations.length === 0) return null;
  return (
    <section className="citations" aria-label="Sources">
      <h3 className="citations__title">Sources</h3>
      <ol className="citations__list">
        {citations.map((c) => {
          const href = safeHttpsUrl(c.url);
          return (
            <li key={c.chunk_id} className="citation">
              {href ? (
                <a href={href} target="_blank" rel="noopener noreferrer">
                  {c.title}
                </a>
              ) : (
                <span>{c.title}</span>
              )}
              <span className="citation__meta">
                {c.approval_status && (
                  <span className={`badge badge--${c.approval_status}`}>{APPROVAL_LABEL[c.approval_status]}</span>
                )}
                {c.freshness && (
                  <span className={`badge badge--fresh-${c.freshness}`}>{FRESHNESS_LABEL[c.freshness]}</span>
                )}
                <span className="citation__version" title="Content version">
                  v{c.version}
                </span>
              </span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
