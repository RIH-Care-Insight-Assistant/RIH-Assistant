"""Pydantic request/response models: the single schema source for OpenAPI and the frontend.

Contract: docs/contracts/C2-local-v1.md. Requests reject unknown fields.
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_MESSAGE_CHARS = 4000

SafetyLane = Literal["urgent_safety", "title_ix", "harassment_hate"]
ResponseType = Literal["safety", "answer", "clarification", "alternatives", "fallback", "guidance"]
Rating = Literal["helpful", "not_helpful"]
Freshness = Literal["fresh", "aging", "stale", "expired", "unknown"]
ApprovalStatus = Literal["approved", "baseline", "pending", "rejected", "retired"]


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorEnvelope(BaseModel):
    error: ErrorBody


class Health(BaseModel):
    status: Literal["ok"]
    api_version: Literal["v1"]


class ReadyChecks(BaseModel):
    database: Literal["ok", "unavailable"]
    knowledge_base: Literal["ok", "unavailable"]
    policy: Literal["ok", "unavailable"]


class Ready(BaseModel):
    status: Literal["ready", "degraded"]
    checks: ReadyChecks


class Citation(BaseModel):
    source_id: str
    chunk_id: str
    title: str
    url: str
    version: str
    approval_status: Optional[ApprovalStatus]
    approved_at: Optional[str]
    checked_at: Optional[str]
    freshness: Optional[Freshness]


class ClarificationOption(BaseModel):
    id: str
    label: str


class Clarification(BaseModel):
    prompt: str
    options: List[ClarificationOption]


class Notice(BaseModel):
    kind: Literal["stale_source", "baseline_source", "no_eligible_source", "degraded"]
    message: str


class Session(BaseModel):
    id: str
    title: Optional[str]
    created_at: str
    updated_at: str


class SessionList(BaseModel):
    items: List[Session]


class Message(BaseModel):
    id: str
    session_id: str
    role: Literal["user", "assistant"]
    text: str
    created_at: str
    citations: List[Citation]
    safety_lane: Optional[SafetyLane]
    response_type: Optional[ResponseType]
    clarification: Optional[Clarification]


class MessagePage(BaseModel):
    items: List[Message]
    next_cursor: Optional[str]


class CreateSession(StrictRequest):
    pass


class ChatRequest(StrictRequest):
    session_id: str = Field(min_length=1, max_length=64)
    message: Optional[str] = Field(default=None, max_length=MAX_MESSAGE_CHARS * 2)
    clarification_option_id: Optional[str] = Field(default=None, max_length=64)

    @field_validator("message")
    @classmethod
    def _message_length(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped or len(stripped) > MAX_MESSAGE_CHARS:
            raise ValueError("message must be 1-4000 characters")
        return stripped

    @model_validator(mode="after")
    def _exactly_one(self) -> "ChatRequest":
        if (self.message is None) == (self.clarification_option_id is None):
            raise ValueError("send exactly one of message or clarification_option_id")
        return self


class ChatResponse(BaseModel):
    session_id: str
    user_message: Message
    message: Message
    response_type: ResponseType
    safety_lane: Optional[SafetyLane]
    is_terminal_safety: bool
    citations: List[Citation]
    clarification: Optional[Clarification]
    notices: List[Notice]
    persisted: bool


class Provenance(BaseModel):
    source_id: str
    version: str
    content_sha256: str
    updated_on: Optional[str]
    approval_status: Optional[ApprovalStatus]
    approved_at: Optional[str]
    approved_by: Optional[str]
    checked_at: Optional[str]
    expires_at: Optional[str]
    freshness: Optional[Freshness]


class Resource(BaseModel):
    id: str
    title: str
    url: str
    category: str
    provenance: Provenance


class ResourceList(BaseModel):
    items: List[Resource]


class FeedbackRequest(StrictRequest):
    session_id: str = Field(min_length=1, max_length=64)
    message_id: str = Field(min_length=1, max_length=64)
    rating: Rating


class Feedback(BaseModel):
    id: str
    session_id: str
    message_id: str
    rating: Rating
    created_at: str
