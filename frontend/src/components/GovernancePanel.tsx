import { useCallback, useEffect, useState } from "react";
import { ApiError, staffApi } from "../api/client";
import type { Readiness, RiskItem } from "../api/types";

const STATUS_LABEL: Record<Readiness["status"], string> = {
  ready: "Ready (an admin may record an approval)",
  not_ready: "Not ready",
  blocked_pending_human_decision: "Blocked: human decisions pending",
};

function message(err: unknown): string {
  if (err instanceof ApiError && err.status === 403) return "The server refused this action for your role or the current state.";
  if (err instanceof ApiError && err.status === 422) return "Check the form: a rationale of at least 10 characters is required.";
  return err instanceof ApiError ? err.message : "Something went wrong.";
}

export function GovernancePanel({ isAdmin }: { isAdmin: boolean }) {
  const [risks, setRisks] = useState<RiskItem[] | null>(null);
  const [meta, setMeta] = useState<{ framework: string; status_note: string; problems: string[] } | null>(null);
  const [ready, setReady] = useState<Readiness | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ risk: "", decision: "confirm_assessment", rationale: "" });
  const [release, setRelease] = useState({ decision: "defer", rationale: "" });
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(() => {
    Promise.all([staffApi.risks(), staffApi.readiness()])
      .then(([r, rd]) => {
        setRisks(r.items);
        setMeta({ framework: r.framework, status_note: r.status_note, problems: r.integrity_problems });
        setReady(rd);
      })
      .catch((err) => setError(message(err)));
  }, []);
  useEffect(load, [load]);

  if (error) return <p className="error-banner" role="alert">{error}</p>;
  if (!risks || !ready || !meta) return <p role="status">Loading governance records…</p>;

  return (
    <div className="governance">
      <section aria-labelledby="readiness-title" className={`readiness readiness--${ready.status}`}>
        <h3 id="readiness-title">Release readiness: {STATUS_LABEL[ready.status]}</h3>
        {ready.candidate && <p className="muted">Candidate {ready.candidate} · evidence {ready.evidence_generated_at}</p>}
        {ready.redteam && (
          <p>
            Adversarial suite ({ready.redteam.label}): {ready.redteam.attack_successes}/{ready.redteam.attempted} attacks
            succeeded; critical open: {ready.redteam.critical_open.length || "none"}.
          </p>
        )}
        {ready.blockers.length > 0 && (
          <>
            <h4>Blockers</h4>
            <ul>{ready.blockers.map((b) => <li key={b}>{b}</li>)}</ul>
          </>
        )}
        {ready.pending_human_decisions.length > 0 && (
          <>
            <h4>Decisions waiting for a person</h4>
            <ul>{ready.pending_human_decisions.map((p) => <li key={p.risk + p.reason}>{p.risk}: {p.reason}</li>)}</ul>
          </>
        )}
        {ready.checks.length > 0 && (
          <ul className="plain-list">
            {ready.checks.map((c) => <li key={c.id}>{c.id}: <strong>{c.status}</strong>{c.detail ? ` · ${c.detail}` : ""}</li>)}
          </ul>
        )}
      </section>

      <p className="muted">{meta.framework} {meta.status_note}</p>
      {meta.problems.length > 0 && (
        <p className="error-banner" role="alert">Register integrity problems: {meta.problems.join("; ")}</p>
      )}
      {notice && <p role="status">{notice}</p>}

      <div className="table-wrap">
        <table className="table">
          <caption>Risk register: inherent and residual scores (likelihood × severity), controls, red-team findings and human decisions.</caption>
          <thead>
            <tr>
              <th scope="col">Risk</th><th scope="col">Inherent</th><th scope="col">Residual</th><th scope="col">Status</th>
              <th scope="col">Controls</th><th scope="col">Findings</th><th scope="col">Human decision</th>
            </tr>
          </thead>
          <tbody>
            {risks.map((r) => (
              <tr key={r.id}>
                <td>
                  <strong>{r.id}</strong> {r.title}<div className="muted">{r.category} · {r.nist.join(", ")} · {r.proposed_owner}</div>
                  {(r.pending_human_review ?? []).length > 0 && (
                    <ul className="muted" aria-label={`Awaiting human review for ${r.id}`}>
                      {(r.pending_human_review ?? []).map((item) => <li key={item}>Awaiting human review: {item}</li>)}
                    </ul>
                  )}
                </td>
                <td>{r.inherent_score} ({r.inherent_band})</td>
                <td>{r.residual_score} ({r.residual_band})</td>
                <td>{r.mitigation_status}</td>
                <td className="muted">{r.controls.join(", ")}</td>
                <td>{r.findings.join(", ") || "—"}</td>
                <td>{r.human_decision ? `${r.human_decision.decision} by ${r.human_decision.reviewer}` : "none recorded"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <form
        className="inline-form"
        onSubmit={async (e) => {
          e.preventDefault();
          setNotice(null);
          try {
            await staffApi.reviewRisk(form.risk, form.decision, form.rationale);
            setNotice(`Recorded your decision on ${form.risk}.`);
            setForm({ ...form, rationale: "" });
            load();
          } catch (err) {
            setNotice(message(err));
          }
        }}
      >
        <h4>Record a risk review</h4>
        <label htmlFor="review-risk">Risk</label>
        <select id="review-risk" value={form.risk} onChange={(e) => setForm({ ...form, risk: e.target.value })} required>
          <option value="">Choose…</option>
          {risks.map((r) => <option key={r.id} value={r.id}>{r.id} {r.title}</option>)}
        </select>
        <label htmlFor="review-decision">Decision</label>
        <select id="review-decision" value={form.decision} onChange={(e) => setForm({ ...form, decision: e.target.value })}>
          <option value="confirm_assessment">Confirm assessment</option>
          <option value="accept_residual">Accept residual risk</option>
          <option value="require_mitigation">Require further mitigation</option>
          <option value="reopen">Reopen</option>
        </select>
        <label htmlFor="review-rationale">Rationale</label>
        <textarea id="review-rationale" value={form.rationale} maxLength={1000} rows={2}
          onChange={(e) => setForm({ ...form, rationale: e.target.value })} required />
        <button type="submit" className="btn btn--primary">Record review</button>
      </form>

      {isAdmin && (
        <form
          className="inline-form"
          onSubmit={async (e) => {
            e.preventDefault();
            setNotice(null);
            try {
              await staffApi.releaseDecision(release.decision, release.rationale, ready.snapshot_sha256);
              setNotice("Release decision recorded.");
              load();
            } catch (err) {
              setNotice(message(err));
            }
          }}
        >
          <h4>Release decision (admin)</h4>
          <label htmlFor="release-decision">Decision</label>
          <select id="release-decision" value={release.decision} onChange={(e) => setRelease({ ...release, decision: e.target.value })}>
            <option value="defer">Defer</option>
            <option value="reject">Reject</option>
            <option value="approve" disabled={ready.status !== "ready"}>Approve (only when ready)</option>
          </select>
          <label htmlFor="release-rationale">Rationale</label>
          <textarea id="release-rationale" value={release.rationale} maxLength={1000} rows={2}
            onChange={(e) => setRelease({ ...release, rationale: e.target.value })} required />
          <button type="submit" className="btn btn--primary">Record release decision</button>
        </form>
      )}
    </div>
  );
}
