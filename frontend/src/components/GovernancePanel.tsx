import { useCallback, useEffect, useState } from "react";
import { ApiError, staffApi } from "../api/client";
import type { Readiness, RiskItem, SlotDecision } from "../api/types";
import { Icon } from "./Icon";
import { tone } from "./tone";

const STATUS_LABEL: Record<Readiness["status"], string> = {
  ready: "Ready (both joint reviewers must approve)",
  not_ready: "Not ready",
  blocked_pending_human_decision: "Blocked: human decisions pending",
};

const KIND_LABEL: Record<string, string> = {
  joint_decision: "joint decision",
  review_item: "agent-drafted item",
  specialist_review: "specialist review",
};

function slotText(d: SlotDecision | null): string {
  if (!d) return "none recorded";
  const who = d.reviewer ? ` by ${d.reviewer}` : "";
  return `${d.decision}${who}${d.current ? "" : " (for earlier content of this risk or its controls; not current)"}`;
}

function message(err: unknown): string {
  if (err instanceof ApiError && err.status === 403) {
    return "The server refused this action: only accounts bound to a joint-reviewer slot decide, and approval needs a ready assessment.";
  }
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

  if (error) return <p className="error-banner" role="alert"><Icon name="alert" /><span>{error}</span></p>;
  if (!risks || !ready || !meta) {
    return (
      <p className="loading" role="status">
        <span className="spinner" aria-hidden="true" />
        Loading governance records…
      </p>
    );
  }
  const highResidual = risks.filter((r) => r.residual_band === "high").length;

  return (
    <div className="governance">
      <section aria-labelledby="readiness-title" className={`readiness readiness--${ready.status}`}>
        <div className="readiness__head">
          <div>
            <p className="eyebrow">Release governance</p>
            <h3 id="readiness-title">Release readiness: {STATUS_LABEL[ready.status]}</h3>
          </div>
          <span className={tone(ready.status)}>{ready.status.replace(/_/g, " ")}</span>
        </div>
        <p className="muted">{ready.scope_note}</p>
        {ready.candidate && (
          <p className="muted">
            Candidate {ready.candidate}{ready.candidate_digest ? ` (${ready.candidate_digest.slice(0, 12)})` : ""} · evidence{" "}
            {ready.evidence_generated_at}
          </p>
        )}
        {ready.reviewers && (
          <p className="muted">
            Joint reviewers:{" "}
            {ready.reviewers.configured
              ? ready.reviewers.slots.map((s) => `${s} (${ready.reviewers?.bound[s] ?? "unbound"})`).join(", ")
              : `${ready.reviewers.slots.join(" and ")}, not bound to staff accounts; no decision counts`}
          </p>
        )}
        <dl className="stats">
          <div className="stat"><dt>Risks in register</dt><dd>{risks.length}</dd></div>
          <div className="stat"><dt>High residual risks</dt><dd>{highResidual}</dd></div>
          <div className="stat">
            <dt>Red-team attack successes</dt>
            <dd>{ready.redteam ? `${ready.redteam.attack_successes}/${ready.redteam.attempted}` : "—"}</dd>
          </div>
          <div className="stat stat--accent"><dt>Pending human decisions</dt><dd>{ready.pending_human_decisions.length}</dd></div>
        </dl>
        {ready.redteam && (
          <p className="muted">
            Adversarial suite ({ready.redteam.label}): {ready.redteam.attack_successes}/{ready.redteam.attempted} attacks
            succeeded; critical open: {ready.redteam.critical_open.length || "none"}.
          </p>
        )}
        <div className="readiness__lists">
          {ready.blockers.length > 0 && (
            <div>
              <h4>Blockers</h4>
              <ul>{ready.blockers.map((b) => <li key={b}>{b}</li>)}</ul>
            </div>
          )}
          {ready.pending_human_decisions.length > 0 && (
            <div>
              <h4>Decisions waiting for a person</h4>
              <ul>
                {ready.pending_human_decisions.map((p) => (
                  <li key={p.risk + p.kind + p.reason}>{p.risk} · {KIND_LABEL[p.kind] ?? p.kind}: {p.reason}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
        {ready.checks.length > 0 && (
          <ul className="check-list" aria-label="Release battery checks">
            {ready.checks.map((c) => (
              <li key={c.id}>
                <span>{c.id}{c.detail ? <span className="muted"> · {c.detail}</span> : null}</span>
                <span className={tone(c.status)}>{c.status}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <p className="muted framework-note"><Icon name="info" /><span>{meta.framework} {meta.status_note}</span></p>
      {meta.problems.length > 0 && (
        <p className="error-banner" role="alert">Register integrity problems: {meta.problems.join("; ")}</p>
      )}
      {notice && <p className="notice-banner" role="status">{notice}</p>}

      <div className="table-wrap">
        <table className="table">
          <caption>Risk register: inherent and residual scores (likelihood × severity), controls, red-team findings and each joint reviewer's decision.</caption>
          <thead>
            <tr>
              <th scope="col">Risk</th><th scope="col">Inherent</th><th scope="col">Residual</th><th scope="col">Status</th>
              <th scope="col">Controls</th><th scope="col">Findings</th><th scope="col">Joint decisions</th>
            </tr>
          </thead>
          <tbody>
            {risks.map((r) => (
              <tr key={r.id}>
                <td>
                  <strong>{r.id}</strong> {r.title}<div className="muted">{r.category} · {r.nist.join(", ")} · {r.proposed_owner}</div>
                  {(r.required_specialist_reviews ?? []).length > 0 && (
                    <ul className="muted" aria-label={`Specialist reviews for ${r.id}`}>
                      {(r.required_specialist_reviews ?? []).map((sr) => (
                        <li key={sr.id}>Specialist review ({sr.kind.replace(/_/g, " ")}, {sr.status}): {sr.description}</li>
                      ))}
                    </ul>
                  )}
                  {(r.pending_human_review ?? []).length > 0 && (
                    <ul className="muted" aria-label={`Awaiting human review for ${r.id}`}>
                      {(r.pending_human_review ?? []).map((item) => <li key={item}>Awaiting human review: {item}</li>)}
                    </ul>
                  )}
                </td>
                <td><span className="score"><strong>{r.inherent_score}</strong> <span className={tone(r.inherent_band)}>{r.inherent_band}</span></span></td>
                <td><span className="score"><strong>{r.residual_score}</strong> <span className={tone(r.residual_band)}>{r.residual_band}</span></span></td>
                <td><span className={tone(r.mitigation_status)}>{r.mitigation_status.replace(/_/g, " ")}</span></td>
                <td className="muted">{r.controls.join(", ")}</td>
                <td>{r.findings.join(", ") || "—"}</td>
                <td>
                  <ul className="slot-decisions" aria-label={`Joint decisions for ${r.id}`}>
                    {Object.entries(r.joint_decisions).map(([slot, d]) => <li key={slot}>{slot}: {slotText(d)}</li>)}
                  </ul>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="form-grid">
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
          <p className="muted">Counts only from an account bound to a joint-reviewer slot; approval needs both slots on the same snapshot.</p>
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
    </div>
  );
}
