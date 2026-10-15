import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { resetClientStateForTests } from "../api/client";
import type { RiskItem } from "../api/types";
import { installFakeApi } from "../test/fakeApi";
import { GovernancePanel } from "./GovernancePanel";

const RISK: RiskItem = {
  id: "R-01", title: "Missed crisis", category: "safety", nist: ["Map"], description: "d", proposed_owner: "Abhinav",
  likelihood: 3, severity: 5, residual_likelihood: 2, residual_severity: 5, inherent_score: 15, inherent_band: "high",
  residual_score: 10, residual_band: "medium", controls: ["C-SAFETY-FIRST"], findings: ["SB-07"],
  mitigation_status: "partially_mitigated", mitigation_plan: "p", evidence: [], decision_version: "risks-1#0/controls-1#0",
  joint_decisions: { abhinav: null, devika: null },
};

beforeEach(() => resetClientStateForTests());

describe("GovernancePanel", () => {
  it("shows readiness blockers, risks without pre-filled decisions, and records a review", async () => {
    const api = installFakeApi({ staff: { username: "rita.reviewer", roles: ["reviewer"] }, risks: [RISK] });
    const user = userEvent.setup();
    render(<GovernancePanel isAdmin={false} />);
    expect(await screen.findByRole("heading", { name: /Release readiness: Not ready/ })).toBeInTheDocument();
    expect(screen.getByText("release battery evidence is missing")).toBeInTheDocument();
    expect(screen.getByRole("list", { name: "Joint decisions for R-01" })).toHaveTextContent(
      "abhinav: none recordeddevika: none recorded");
    expect(screen.getByText(/abhinav and devika, not bound to staff accounts; no decision counts/)).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Release decision (admin)" })).not.toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText("Risk"), "R-01");
    await user.selectOptions(screen.getByLabelText("Decision"), "accept_residual");
    await user.type(screen.getByLabelText("Rationale"), "Synthetic rationale for the test.");
    await user.click(screen.getByRole("button", { name: "Record review" }));
    await waitFor(() => expect(api.reviews).toHaveLength(1));
    expect(api.reviews[0]).toEqual({ path: "/admin/governance/risks/R-01/reviews",
      body: { decision: "accept_residual", rationale: "Synthetic rationale for the test." } });
  });

  it("lists agent-drafted mitigations that await human review", async () => {
    const pending = { ...RISK, pending_human_review: ["synthetic agent-drafted term list"] };
    installFakeApi({ staff: { username: "rita.reviewer", roles: ["reviewer"] }, risks: [pending] });
    render(<GovernancePanel isAdmin={false} />);
    const list = await screen.findByRole("list", { name: "Awaiting human review for R-01" });
    expect(list).toHaveTextContent("Awaiting human review: synthetic agent-drafted term list");
  });

  it("shows each joint reviewer's own decision and marks one for earlier content as not current", async () => {
    const decision = { decision: "accept_residual", reviewer: "rita.reviewer", decided_at: "2026-10-15T00:00:00Z",
      decision_version: "risks-2#0000000000000000/controls-2#0", current: false };
    const rejected = { ...decision, decision: "require_mitigation", reviewer: "dana.admin", current: true };
    const risk = { ...RISK, joint_decisions: { abhinav: decision, devika: rejected } };
    installFakeApi({ staff: { username: "rita.reviewer", roles: ["reviewer"] }, risks: [risk] });
    render(<GovernancePanel isAdmin={false} />);
    const list = await screen.findByRole("list", { name: "Joint decisions for R-01" });
    expect(list).toHaveTextContent(
      "abhinav: accept_residual by rita.reviewer (for earlier content of this risk or its controls; not current)");
    expect(list).toHaveTextContent("devika: require_mitigation by dana.admin");
  });

  it("lists mandatory specialist reviews separately from agent-drafted items", async () => {
    const risk = { ...RISK, required_specialist_reviews: [
      { id: "SR-1", kind: "native_speaker", description: "synthetic lexicon check", status: "required" as const }] };
    installFakeApi({ staff: { username: "rita.reviewer", roles: ["reviewer"] }, risks: [risk] });
    render(<GovernancePanel isAdmin={false} />);
    const list = await screen.findByRole("list", { name: "Specialist reviews for R-01" });
    expect(list).toHaveTextContent("Specialist review (native speaker, required): synthetic lexicon check");
  });

  it("offers approval to admins only when the assessment is ready", async () => {
    installFakeApi({ staff: { username: "adam.admin", roles: ["admin"] }, risks: [RISK] });
    render(<GovernancePanel isAdmin />);
    expect(await screen.findByRole("heading", { name: "Release decision (admin)" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Approve (only when ready)" })).toBeDisabled();
  });
});
