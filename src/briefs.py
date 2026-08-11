from __future__ import annotations

from dataclasses import dataclass

from src.domain import EvidenceRecord, ReviewStatus


@dataclass(frozen=True)
class BriefSentence:
    text: str
    evidence_id: str


@dataclass(frozen=True)
class Brief:
    mode: str
    sentences: list[BriefSentence]


def _sentence(item: EvidenceRecord) -> BriefSentence:
    return BriefSentence(f"{item.claim}（来源：{item.source_title}）", item.id)


def build_preview(evidence: list[EvidenceRecord]) -> Brief:
    candidates = [item for item in evidence if item.can_confirm and item.review_status in {ReviewStatus.PENDING, ReviewStatus.NEEDS_EDIT, ReviewStatus.CONFIRMED}]
    return Brief("preview", [_sentence(item) for item in candidates])


def build_formal(evidence: list[EvidenceRecord]) -> Brief:
    return Brief("formal", [_sentence(item) for item in evidence if item.review_status is ReviewStatus.CONFIRMED and item.can_confirm])


def validate_sentence_maps(brief: Brief, evidence: list[EvidenceRecord]) -> list[str]:
    allowed = {item.id for item in evidence if item.review_status is ReviewStatus.CONFIRMED and item.can_confirm}
    return [sentence.evidence_id for sentence in brief.sentences if sentence.evidence_id not in allowed]
