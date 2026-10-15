// Mirrors contracts/openapi-v1.json (contract C2-local-v1). Field names are checked
// against the snapshot by tests/api/test_openapi_contract.py.

export type SafetyLane = "urgent_safety" | "title_ix" | "harassment_hate";
export type ResponseType = "safety" | "answer" | "clarification" | "alternatives" | "fallback" | "guidance";
export type Rating = "helpful" | "not_helpful";
export type Freshness = "fresh" | "aging" | "stale" | "expired" | "unknown";
export type ApprovalStatus = "approved" | "baseline" | "pending" | "rejected" | "retired";

export interface ErrorBody {
  code: string;
  message: string;
  request_id: string;
}

export interface Session {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  source_id: string;
  chunk_id: string;
  title: string;
  url: string;
  version: string;
  approval_status: ApprovalStatus | null;
  approved_at: string | null;
  checked_at: string | null;
  freshness: Freshness | null;
}

export interface ClarificationOption {
  id: string;
  label: string;
}

export interface Clarification {
  prompt: string;
  options: ClarificationOption[];
}

export interface Notice {
  kind: "stale_source" | "baseline_source" | "no_eligible_source" | "degraded";
  message: string;
}

export interface Message {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  text: string;
  created_at: string;
  citations: Citation[];
  safety_lane: SafetyLane | null;
  response_type: ResponseType | null;
  clarification: Clarification | null;
}

export interface MessagePage {
  items: Message[];
  next_cursor: string | null;
}

export interface ChatResponse {
  session_id: string;
  user_message: Message;
  message: Message;
  response_type: ResponseType;
  safety_lane: SafetyLane | null;
  is_terminal_safety: boolean;
  citations: Citation[];
  clarification: Clarification | null;
  notices: Notice[];
  persisted: boolean;
}

export interface Provenance {
  source_id: string;
  version: string;
  content_sha256: string;
  updated_on: string | null;
  approval_status: ApprovalStatus | null;
  approved_at: string | null;
  approved_by: string | null;
  checked_at: string | null;
  expires_at: string | null;
  freshness: Freshness | null;
}

export interface Resource {
  id: string;
  title: string;
  url: string;
  category: string;
  provenance: Provenance;
}

export interface Feedback {
  id: string;
  session_id: string;
  message_id: string;
  rating: Rating;
  created_at: string;
}

// ---- Staff (Phase 4). Admin routes are role-checked on the server; these are display types.

export interface StaffUser {
  username: string;
  roles: string[];
}

export interface Me {
  authenticated: boolean;
  user: StaffUser | null;
}

export interface SourceRow {
  chunk_id: string;
  title: string;
  url: string;
  category: string;
  version: string;
  updated_on: string | null;
  ingested: boolean;
  inventory_status: string | null;
  effective_status: string | null;
  freshness: string | null;
  eligible: boolean;
  reasons: string[];
  signals: string[];
  approved_by: string | null;
  approved_at: string | null;
}

export interface AuditEvent {
  seq: number;
  ts: string;
  category: string;
  principal_hash: string | null;
  roles: string;
  action: string | null;
  resource: string | null;
  via: string | null;
  allowed: boolean | null;
  rule_id: string | null;
  detail: string | null;
}

export interface UserRow {
  id: string;
  username: string;
  roles: string[];
  disabled: boolean;
  created_at: string;
}

// ---- Governance (Phase 6)

export interface HumanDecision {
  decision: string;
  rationale: string;
  reviewer: string;
  reviewer_roles: string;
  decided_at: string;
  register_version: string;
}

export interface RiskItem {
  id: string;
  title: string;
  category: string;
  nist: string[];
  description: string;
  proposed_owner: string;
  likelihood: number;
  severity: number;
  residual_likelihood: number;
  residual_severity: number;
  inherent_score: number;
  inherent_band: string;
  residual_score: number;
  residual_band: string;
  controls: string[];
  findings: string[];
  mitigation_status: string;
  mitigation_plan: string;
  evidence: string[];
  human_decision: HumanDecision | null;
}

export interface Readiness {
  status: "ready" | "not_ready" | "blocked_pending_human_decision";
  register_version: string;
  candidate: string | null;
  blockers: string[];
  pending_human_decisions: { risk: string; reason: string }[];
  redteam: { label: string; attempted: number; attack_successes: number; attack_success_rate: number; critical_open: string[] } | null;
  checks: { id: string; status: string; required?: boolean; detail?: string }[];
  evidence_generated_at: string | null;
  snapshot_sha256: string;
}
