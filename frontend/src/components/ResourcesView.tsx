import { useEffect, useState } from "react";
import { api, ApiError, safeHttpsUrl } from "../api/client";
import type { Resource } from "../api/types";
import { Icon } from "./Icon";

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
    <section className="resources card" aria-labelledby="resources-title">
      <div className="page-header">
        <div>
          <p className="eyebrow">Directory</p>
          <h2 id="resources-title">Campus resources</h2>
          <p>Pages the assistant may cite. Each entry shows where it came from and its review status.</p>
        </div>
      </div>
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
        <label htmlFor="resource-q" className="visually-hidden">
          Search resources
        </label>
        <div className="search-field">
          <Icon name="search" />
          <input id="resource-q" className="input" type="search" value={query} maxLength={512}
            placeholder="Search by topic, for example immunizations" onChange={(e) => setQuery(e.target.value)} />
        </div>
        <button type="submit" className="btn btn--primary">
          Search
        </button>
      </form>
      {error && (
        <div className="error-banner" role="alert">
          <Icon name="alert" />
          <span>{error}</span>
        </div>
      )}
      {items === null ? (
        <>
          <p className="loading" role="status">
            <span className="spinner" aria-hidden="true" />
            Loading resources…
          </p>
          <ul className="skeleton-grid" aria-hidden="true">
            {[0, 1, 2].map((i) => <li key={i} className="skeleton" />)}
          </ul>
        </>
      ) : items.length === 0 ? (
        <div className="empty-state">
          <span className="empty-state__icon" aria-hidden="true">
            <Icon name="search" />
          </span>
          <strong>No matching approved resources.</strong>
          <p>Try a broader word such as hours, billing or counseling.</p>
        </div>
      ) : (
        <>
          <p className="resources__summary">
            {items.length} {items.length === 1 ? "resource" : "resources"}
            {submitted ? ` matching “${submitted}”` : ""}
          </p>
          <ul className="resource-list">
            {items.map((r) => {
              const href = safeHttpsUrl(r.url);
              const status = r.provenance.approval_status;
              const fresh = r.provenance.freshness;
              return (
                <li key={r.id} className="resource">
                  <div className="resource__top">
                    <span className="resource__category">{r.category || "General"}</span>
                    {fresh && <span className={`badge badge--fresh-${fresh}`}>{fresh}</span>}
                  </div>
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
                    <dt>Page updated</dt>
                    <dd>{r.provenance.updated_on ?? "unknown"}</dd>
                    <dt>Review status</dt>
                    <dd>
                      {status ? <span className={`badge badge--${status}`}>{status}</span> : "not assessed"}
                    </dd>
                    <dt>Version</dt>
                    <dd className="mono">{r.provenance.version}</dd>
                  </dl>
                </li>
              );
            })}
          </ul>
        </>
      )}
    </section>
  );
}
