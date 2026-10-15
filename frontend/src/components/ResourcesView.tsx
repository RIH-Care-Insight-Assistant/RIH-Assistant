import { useEffect, useState } from "react";
import { api, ApiError, safeHttpsUrl } from "../api/client";
import type { Resource } from "../api/types";

export function ResourcesView() {
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState("");
  const [items, setItems] = useState<Resource[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    api
      .resources(submitted, ctrl.signal)
      .then((r) => setItems(r.items))
      .catch((err: unknown) => {
        if ((err as Error).name === "AbortError") return;
        setError(err instanceof ApiError ? err.message : "Something went wrong.");
        setItems([]);
      });
    return () => ctrl.abort();
  }, [submitted]);

  return (
    <section className="resources" aria-labelledby="resources-title">
      <h2 id="resources-title">Campus resources</h2>
      <p className="resources__intro">
        Pages the assistant may cite. Each entry shows where it came from and its review status.
      </p>
      <form
        role="search"
        className="resources__search"
        onSubmit={(e) => {
          e.preventDefault();
          const next = query.trim();
          if (next === submitted) return;
          setItems(null);
          setError(null);
          setSubmitted(next);
        }}
      >
        <label htmlFor="resource-q">Search resources</label>
        <input id="resource-q" type="search" value={query} maxLength={512} onChange={(e) => setQuery(e.target.value)} />
        <button type="submit" className="btn btn--primary">
          Search
        </button>
      </form>
      {error && (
        <div className="error-banner" role="alert">
          {error}
        </div>
      )}
      {items === null ? (
        <p role="status">Loading resources…</p>
      ) : items.length === 0 ? (
        <p className="empty">No matching approved resources.</p>
      ) : (
        <ul className="resource-list">
          {items.map((r) => {
            const href = safeHttpsUrl(r.url);
            return (
              <li key={r.id} className="resource">
                <h3 className="resource__title">
                  {href ? (
                    <a href={href} target="_blank" rel="noopener noreferrer">
                      {r.title}
                    </a>
                  ) : (
                    r.title
                  )}
                </h3>
                <dl className="resource__meta">
                  <dt>Category</dt>
                  <dd>{r.category || "—"}</dd>
                  <dt>Page updated</dt>
                  <dd>{r.provenance.updated_on ?? "unknown"}</dd>
                  <dt>Review status</dt>
                  <dd>{r.provenance.approval_status ?? "not assessed"}</dd>
                  <dt>Freshness</dt>
                  <dd>{r.provenance.freshness ?? "not assessed"}</dd>
                  <dt>Version</dt>
                  <dd>{r.provenance.version}</dd>
                </dl>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
