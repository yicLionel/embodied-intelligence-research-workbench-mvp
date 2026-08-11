from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ReviewStatus(StrEnum):
    PENDING = "pending"
    NEEDS_EDIT = "needs_edit"
    CONFIRMED = "confirmed"
    DISCARDED = "discarded"


class RiskFlag(StrEnum):
    BLOCKED = "blocked"
    CONFLICT = "conflict"
    POSSIBLY_STALE = "possibly_stale"
    INCOMPLETE = "incomplete"
    MISSING_EVIDENCE = "missing_evidence"


class Project(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    topic: str = "具身智能"
    geography: str = "中国为主，全球对照"
    time_range: str = "2024–2026"
    purpose: str = "内部项目讨论"
    focus_questions: str = ""


class ResearchQuestion(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    project_id: str
    dimension: str
    text: str
    priority: int = Field(ge=1, le=3)
    approved: bool = False
    deleted: bool = False


class SourceRecord(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    project_id: str
    title: str
    organization: str
    source_role: str
    publication_date: date
    url: str | None = None
    reference: str | None = None
    accessible: bool = True
    extraction_status: str = "success"
    excluded: bool = False


class EvidenceRecord(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    project_id: str
    question_id: str
    dimension: str
    claim: str
    source_id: str
    source_title: str
    source_url: str | None = None
    source_reference: str | None = None
    source_accessible: bool
    publication_date: date
    evidence_quote: str = ""
    geography: str | None = None
    period: str | None = None
    unit: str | None = None
    definition_scope: str | None = None
    category: str
    risk_flags: list[str] = Field(default_factory=list)
    review_status: ReviewStatus = ReviewStatus.PENDING

    @property
    def can_confirm(self) -> bool:
        return bool(
            self.source_accessible
            and self.evidence_quote.strip()
            and (self.source_url or self.source_reference)
            and self.review_status is not ReviewStatus.DISCARDED
        )

    def with_status(self, status: ReviewStatus) -> EvidenceRecord:
        if status is ReviewStatus.CONFIRMED and not self.can_confirm:
            return self
        return self.model_copy(update={"review_status": status})
