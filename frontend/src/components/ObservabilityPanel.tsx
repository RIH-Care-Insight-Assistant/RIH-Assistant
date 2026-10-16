import { useCallback, useEffect, useState } from "react";
import { ApiError, staffApi } from "../api/client";
import { Icon } from "./Icon";

interface Summary {
  uptime_s: number;
  requests_by_class: Record<string, number>;
  latency_by_route: Record<string, { count: number; p50_ms: number; p95_ms: number; max_ms: number }>;
  tool_calls_by_status: Record<string, number>;
  chat_turns_by_lane: Record<string, number>;
  security_events: Record<string, number>;
  planner_outcomes: Record<string, number>;
  recent_spans: { name: string; trace_id: string; duration_ms: number; status: string; attributes: Record<string, unknown> }[];
}

interface Incident {
  id: string;
  scenario: string;
  severity: string;
  started_at: string;
  detected_by: string[];
  outcome: string;
  synthetic_request_statuses: number[];
}

const sum = (data: Record<string, number>) => Object.values(data).reduce((a, b) => a + b, 0);

function Counts({ title, data }: { title: string; data: Record<string, number> }) {
  const entries = Object.entries(data).sort((x, y) => y[1] - x[1]);
  const max = Math.max(1, ...entries.map(([, v]) => v));
  return (
    <div className="count-card">
      <h4>{title}</h4>
      {entries.length === 0 ? <p className="muted">none yet</p> : (
        <dl>
          {entries.map(([k, v]) => (
            <div key={k}>
              <dt>{k}</dt>
              <dd>{v}</dd>
              {/* Proportional bar drawn with SVG attributes, so it works under the strict style CSP. */}
              <svg className="bar" viewBox="0 0 100 6" preserveAspectRatio="none" aria-hidden="true" focusable="false">
                <rect className="bar__track" x="0" y="0" width="100" height="6" rx="3" />
                <rect className="bar__fill" x="0" y="0" width={Math.max(2, (v / max) * 100)} height="6" rx="3" />
              </svg>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}

function uptime(seconds: number): string {
  const s = Math.round(seconds);
  if (s < 120) return `${s} s`;
  const m = Math.round(s / 60);
  return m < 120 ? `${m} min` : `${Math.round(m / 60)} h`;
}

export function ObservabilityPanel({ isAdmin }: { isAdmin: boolean }) {
  const [s, setS] = useState<Summary | null>(null);
  const [incidents, setIncidents] = useState<{ simulation_enabled: boolean; items: Incident[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [scenario, setScenario] = useState("database_outage");
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(() => {
    staffApi.observability().then(setS).catch((err) => setError(err instanceof ApiError ? err.message : "Unavailable."));
    if (isAdmin) staffApi.incidents().then(setIncidents).catch(() => setIncidents(null));
  }, [isAdmin]);
  useEffect(load, [load]);

  if (error) return <p className="error-banner" role="alert"><Icon name="alert" /><span>{error}</span></p>;
  if (!s) {
    return (
      <p className="loading" role="status">
        <span className="spinner" aria-hidden="true" />
        Loading telemetry…
      </p>
    );
  }

  return (
    <div className="observability">
      <p className="panel-intro">
        Aggregates only: no message text, identities or raw paths are recorded.
      </p>
      <dl className="stats">
        <div className="stat stat--accent"><dt>Requests</dt><dd>{sum(s.requests_by_class)}</dd></div>
        <div className="stat"><dt>Chat turns</dt><dd>{sum(s.chat_turns_by_lane)}</dd></div>
        <div className="stat"><dt>Governed tool calls</dt><dd>{sum(s.tool_calls_by_status)}</dd></div>
        <div className="stat"><dt>Security events</dt><dd>{sum(s.security_events)}</dd></div>
        <div className="stat"><dt>Process uptime</dt><dd>{uptime(s.uptime_s)}</dd></div>
      </dl>
      <div className="count-grid">
        <Counts title="Requests by class" data={s.requests_by_class} />
        <Counts title="Chat turns by safety lane" data={s.chat_turns_by_lane} />
        <Counts title="Tool calls by status" data={s.tool_calls_by_status} />
        <Counts title="Security events" data={s.security_events} />
        <Counts title="Model planner outcomes" data={s.planner_outcomes} />
      </div>
      <div className="table-wrap">
        <table className="table">
          <caption>Latency per route (nearest-rank percentiles over recent requests)</caption>
          <thead>
            <tr>
              <th scope="col">Route</th><th scope="col" className="num">Count</th><th scope="col" className="num">p50 ms</th>
              <th scope="col" className="num">p95 ms</th><th scope="col" className="num">Max ms</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(s.latency_by_route).map(([route, l]) => (
              <tr key={route}>
                <td className="mono">{route}</td><td className="num">{l.count}</td><td className="num">{l.p50_ms}</td>
                <td className="num">{l.p95_ms}</td><td className="num">{l.max_ms}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <details className="spans">
        <summary>Recent spans ({s.recent_spans.length})</summary>
        <ul className="plain-list">
          {s.recent_spans.map((sp, i) => (
            <li key={sp.trace_id + i}>
              <code>{sp.name}</code> {sp.duration_ms} ms {sp.status !== "UNSET" ? sp.status : ""}{" "}
              <span className="muted">{Object.entries(sp.attributes).map(([k, v]) => `${k}=${String(v)}`).join(" ")}</span>
            </li>
          ))}
        </ul>
      </details>
      {isAdmin && incidents && (
        <section aria-labelledby="incidents-title" className="incidents">
          <h4 id="incidents-title">Incident simulations</h4>
          {incidents.simulation_enabled ? (
            <form className="inline-form" onSubmit={async (e) => {
              e.preventDefault();
              setNotice(null);
              try {
                const r = await staffApi.simulateIncident(scenario);
                setNotice(`Simulation ${r.outcome}; detected by: ${r.detected_by.join(", ")}`);
                load();
              } catch (err) {
                setNotice(err instanceof ApiError ? err.message : "Simulation failed.");
              }
            }}>
              <label htmlFor="incident-scenario">Scenario (synthetic, in-process)</label>
              <select id="incident-scenario" value={scenario} onChange={(e) => setScenario(e.target.value)}>
                <option value="database_outage">Database outage</option>
                <option value="retrieval_outage">Retrieval outage</option>
                <option value="authz_denial_spike">Authorization denial spike</option>
              </select>
              <button type="submit" className="btn btn--primary">Run simulation</button>
            </form>
          ) : <p className="muted">Simulation is disabled in this environment.</p>}
          {notice && <p className="notice-banner" role="status">{notice}</p>}
          <ul className="plain-list">
            {incidents.items.map((i) => (
              <li key={i.id}>{i.started_at} · {i.scenario} ({i.severity}) · {i.outcome} · statuses {i.synthetic_request_statuses.join(", ")} · detected by {i.detected_by.join("; ")}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
