import { useCallback, useEffect, useState } from "react";
import { ApiError, staffApi } from "../api/client";
import type { AuditEvent, Me, SourceRow, UserRow } from "../api/types";
import { GovernancePanel } from "./GovernancePanel";
import { Icon } from "./Icon";
import { ObservabilityPanel } from "./ObservabilityPanel";
import { tone } from "./tone";

type Tab = "sources" | "governance" | "observability" | "feedback" | "users" | "audit" | "ingest";

function errorText(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 403) return "Your role does not allow this. The server refused the request.";
    if (err.status === 401) return "Your staff session has ended. Please sign in again.";
    if (err.code === "rate_limited") return "Too many attempts. Please wait and try again.";
    return err.message;
  }
  return "Something went wrong.";
}

function Loading({ label }: { label: string }) {
  return (
    <p className="loading" role="status">
      <span className="spinner" aria-hidden="true" />
      {label}
    </p>
  );
}

function ErrorBanner({ text }: { text: string }) {
  return (
    <p className="error-banner" role="alert">
      <Icon name="alert" />
      <span>{text}</span>
    </p>
  );
}

function LoginForm({ onLogin }: { onLogin: (me: Me) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  return (
    <form
      className="login"
      onSubmit={async (e) => {
        e.preventDefault();
        setBusy(true);
        setError(null);
        try {
          onLogin(await staffApi.login(username, password));
        } catch (err) {
          setError(err instanceof ApiError && err.status === 401 ? "Sign-in failed." : errorText(err));
        } finally {
          setPassword("");
          setBusy(false);
        }
      }}
    >
      <h3>
        <Icon name="lock" />
        Staff sign-in
      </h3>
      {error && <ErrorBanner text={error} />}
      <label htmlFor="staff-username">Username</label>
      <input id="staff-username" autoComplete="username" value={username} maxLength={64}
        onChange={(e) => setUsername(e.target.value)} required />
      <label htmlFor="staff-password">Password</label>
      <input id="staff-password" type="password" autoComplete="current-password" value={password} maxLength={256}
        onChange={(e) => setPassword(e.target.value)} required />
      <button type="submit" className="btn btn--primary" disabled={busy}>
        Sign in
      </button>
    </form>
  );
}

function SourcesPanel() {
  const [rows, setRows] = useState<SourceRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const load = useCallback(() => {
    staffApi.sources().then((r) => setRows(r.items)).catch((err) => setError(errorText(err)));
  }, []);
  useEffect(load, [load]);

  const decide = async (row: SourceRow, status: string) => {
    setError(null);
    try {
      await staffApi.review(row.chunk_id, status, notes[row.chunk_id] ?? "");
      load();
    } catch (err) {
      setError(errorText(err));
    }
  };

  if (error) return <ErrorBanner text={error} />;
  if (!rows) return <Loading label="Loading sources…" />;
  return (
    <div className="table-wrap">
      <table className="table">
        <caption>Source review queue: a decision applies to the exact content version shown.</caption>
        <thead>
          <tr>
            <th scope="col">Source</th>
            <th scope="col">Status</th>
            <th scope="col">Freshness</th>
            <th scope="col">Citable</th>
            <th scope="col">Decision</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.chunk_id}>
              <td>
                <strong>{r.title}</strong>
                <div className="muted">{r.url} · v{r.version}{r.ingested ? " · ingested" : ""}</div>
                {r.signals.length > 0 && (
                  <div className="warn">
                    <Icon name="alert" />
                    Instruction-like content: {r.signals.join(", ")}
                  </div>
                )}
              </td>
              <td>
                <span className={tone(r.effective_status)}>{r.effective_status ?? "unknown"}</span>
                {r.approved_by && <div className="muted">by {r.approved_by}</div>}
              </td>
              <td><span className={tone(r.freshness)}>{r.freshness ?? "unknown"}</span></td>
              <td>
                {r.eligible ? (
                  <span className="pill pill--good">Yes</span>
                ) : (
                  <span title={r.reasons.join(", ")}>No ({r.reasons.join(", ")})</span>
                )}
              </td>
              <td>
                <label className="visually-hidden" htmlFor={`note-${r.chunk_id}`}>Review note for {r.title}</label>
                <input id={`note-${r.chunk_id}`} className="note" placeholder="Note (optional)" maxLength={500}
                  value={notes[r.chunk_id] ?? ""} onChange={(e) => setNotes({ ...notes, [r.chunk_id]: e.target.value })} />
                <div className="actions">
                  <button type="button" className="btn btn--small" onClick={() => void decide(r, "approved")}
                    aria-label={`Approve ${r.title}`}>Approve</button>
                  <button type="button" className="btn btn--small btn--danger" onClick={() => void decide(r, "rejected")}
                    aria-label={`Reject ${r.title}`}>Reject</button>
                  <button type="button" className="btn btn--small" onClick={() => void decide(r, "retired")}
                    aria-label={`Retire ${r.title}`}>Retire</button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function FeedbackPanel() {
  const [data, setData] = useState<{ helpful: number; not_helpful: number } | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    staffApi.feedbackSummary().then(setData).catch((err) => setError(errorText(err)));
  }, []);
  if (error) return <ErrorBanner text={error} />;
  if (!data) return <Loading label="Loading…" />;
  const total = data.helpful + data.not_helpful;
  return (
    <>
      <p className="panel-intro">Ratings students gave to individual answers. Counts only; no message text is shown here.</p>
      <dl className="stats">
        <div className="stat stat--accent"><dt>Helpful</dt><dd>{data.helpful}</dd></div>
        <div className="stat"><dt>Not helpful</dt><dd>{data.not_helpful}</dd></div>
        <div className="stat">
          <dt>Share rated helpful</dt>
          <dd>{total ? `${Math.round((data.helpful / total) * 100)}%` : "—"}</dd>
        </div>
      </dl>
    </>
  );
}

function UsersPanel() {
  const [rows, setRows] = useState<UserRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ username: "", password: "", role: "reviewer" });
  const load = useCallback(() => {
    staffApi.users().then((r) => setRows(r.items)).catch((err) => setError(errorText(err)));
  }, []);
  useEffect(load, [load]);
  return (
    <div>
      {error && <ErrorBanner text={error} />}
      <form
        className="inline-form"
        onSubmit={async (e) => {
          e.preventDefault();
          setError(null);
          try {
            await staffApi.createUser(form.username, form.password, [form.role]);
            setForm({ username: "", password: "", role: "reviewer" });
            load();
          } catch (err) {
            setError(err instanceof ApiError && err.status === 422
              ? "Not created: use a 3-32 character lowercase username and a password of at least 12 characters."
              : errorText(err));
          }
        }}
      >
        <h4>Create a staff account</h4>
        <label htmlFor="new-username">Username</label>
        <input id="new-username" value={form.username} maxLength={32}
          onChange={(e) => setForm({ ...form, username: e.target.value })} required />
        <label htmlFor="new-password">Initial password</label>
        <input id="new-password" type="password" autoComplete="new-password" value={form.password} maxLength={256}
          onChange={(e) => setForm({ ...form, password: e.target.value })} required />
        <label htmlFor="new-role">Role</label>
        <select id="new-role" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
          <option value="reviewer">reviewer</option>
          <option value="admin">admin</option>
        </select>
        <button type="submit" className="btn btn--primary">Create account</button>
      </form>
      {rows && (
        <ul className="user-list">
          {rows.map((u) => (
            <li key={u.id} className="user-row">
              <span className="user-row__who">
                <span className="staff-user__avatar" aria-hidden="true">{u.username.slice(0, 2)}</span>
                <span>
                  {u.username} · {u.roles.join(", ")} ·{" "}
                  <span className={tone(u.disabled ? "disabled" : "active")}>{u.disabled ? "disabled" : "active"}</span>
                </span>
              </span>
              {!u.disabled && (
                <button type="button" className="btn btn--small btn--danger" onClick={async () => {
                  try { await staffApi.disableUser(u.id); load(); } catch (err) { setError(errorText(err)); }
                }}>Disable</button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function AuditPanel() {
  const [rows, setRows] = useState<AuditEvent[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    staffApi.audit(100).then((r) => setRows(r.items)).catch((err) => setError(errorText(err)));
  }, []);
  if (error) return <ErrorBanner text={error} />;
  if (!rows) return <Loading label="Loading audit events…" />;
  return (
    <div className="table-wrap">
      <table className="table">
        <caption>Latest policy and security events. Principals are salted hashes; no message text is recorded.</caption>
        <thead>
          <tr><th scope="col">Time</th><th scope="col">Category</th><th scope="col">Action</th><th scope="col">Resource</th>
            <th scope="col">Channel</th><th scope="col">Result</th><th scope="col">Rule</th></tr>
        </thead>
        <tbody>
          {rows.map((e) => (
            <tr key={e.seq}>
              <td className="mono">{e.ts}</td><td>{e.category}</td><td>{e.action ?? ""}</td>
              <td className="mono">{e.resource ?? ""}</td><td>{e.via ?? ""}</td>
              <td>
                {e.allowed === null ? e.detail : (
                  <span className={tone(e.allowed ? "allowed" : "denied")}>{e.allowed ? "allowed" : "denied"}</span>
                )}
              </td>
              <td className="mono">{e.rule_id ?? ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function IngestPanel() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState<string | null>(null);
  return (
    <form
      className="inline-form"
      onSubmit={async (e) => {
        e.preventDefault();
        try {
          const r = await staffApi.ingest(url, "ingested");
          setResult(`Staged as ${r.status}${r.signals.length ? `, quarantined (${r.signals.join(", ")})` : ""}. Review it under Sources.`);
        } catch (err) {
          setResult(errorText(err));
        }
      }}
    >
      <h4>Fetch a page into the review queue</h4>
      <p className="muted">New pages stay pending until a reviewer approves them. Instruction-like content is quarantined.</p>
      <label htmlFor="ingest-url">Official HTTPS page on an allowed host</label>
      <input id="ingest-url" type="url" value={url} maxLength={512} onChange={(e) => setUrl(e.target.value)} required />
      <button type="submit" className="btn btn--primary">
        <Icon name="download" />
        Fetch into review queue
      </button>
      {result && <p role="status">{result}</p>}
    </form>
  );
}

const TABS: { id: Tab; label: string; roles: string[] }[] = [
  { id: "sources", label: "Sources", roles: ["reviewer", "admin"] },
  { id: "governance", label: "Governance", roles: ["reviewer", "admin"] },
  { id: "observability", label: "Observability", roles: ["reviewer", "admin"] },
  { id: "feedback", label: "Feedback", roles: ["reviewer", "admin"] },
  { id: "users", label: "Users", roles: ["admin"] },
  { id: "audit", label: "Audit log", roles: ["admin"] },
  { id: "ingest", label: "Ingest", roles: ["admin"] },
];

export function StaffView() {
  const [me, setMe] = useState<Me | null>(null);
  const [tab, setTab] = useState<Tab>("sources");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    staffApi.me().then(setMe).catch((err) => setError(errorText(err)));
  }, []);

  if (error) return <section className="admin card"><ErrorBanner text={error} /></section>;
  if (!me) return <section className="admin card"><Loading label="Checking access…" /></section>;

  return (
    <section className="admin card" aria-labelledby="admin-title">
      {!me.authenticated || !me.user ? (
        <div className="staff-signin">
          <div className="staff-signin__intro">
            <p className="eyebrow">Reviewers and administrators</p>
            <h2 id="admin-title">Staff area</h2>
            <p>The staff area requires a signed-in reviewer or administrator account. Access is checked by the server.</p>
            <ul className="staff-signin__points">
              <li><Icon name="shieldCheck" /><span>Review sources before students can be shown them.</span></li>
              <li><Icon name="scale" /><span>Record risk reviews and release decisions with a rationale.</span></li>
              <li><Icon name="activity" /><span>Watch aggregate telemetry; no message text or identities are shown.</span></li>
            </ul>
          </div>
          <LoginForm onLogin={setMe} />
        </div>
      ) : (
        <>
          <div className="staff-bar">
            <div>
              <p className="eyebrow">Governed operations</p>
              <h2 id="admin-title">Staff area</h2>
            </div>
            <div className="staff-user">
              <span className="staff-user__avatar" aria-hidden="true">{me.user.username.slice(0, 2)}</span>
              <span>Signed in as <strong>{me.user.username}</strong> ({me.user.roles.join(", ")})</span>
              <button type="button" className="btn btn--small" onClick={async () => {
                await staffApi.logout().catch(() => undefined);
                setMe({ authenticated: false, user: null });
              }}>
                <Icon name="logout" />
                Sign out
              </button>
            </div>
          </div>
          <div role="tablist" aria-label="Staff sections" className="staff-tabs">
            {TABS.filter((t) => t.roles.some((r) => me.user?.roles.includes(r))).map((t) => (
              <button key={t.id} role="tab" type="button" aria-selected={tab === t.id}
                className={tab === t.id ? "tab is-active" : "tab"} onClick={() => setTab(t.id)}>
                {t.label}
              </button>
            ))}
          </div>
          <div role="tabpanel" aria-label={TABS.find((t) => t.id === tab)?.label}>
            {tab === "sources" && <SourcesPanel />}
            {tab === "governance" && <GovernancePanel isAdmin={me.user.roles.includes("admin")} />}
            {tab === "observability" && <ObservabilityPanel isAdmin={me.user.roles.includes("admin")} />}
            {tab === "feedback" && <FeedbackPanel />}
            {tab === "users" && <UsersPanel />}
            {tab === "audit" && <AuditPanel />}
            {tab === "ingest" && <IngestPanel />}
          </div>
        </>
      )}
    </section>
  );
}
