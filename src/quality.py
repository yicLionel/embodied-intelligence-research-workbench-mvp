from __future__ import annotations

from datetime import date

from src.domain import EvidenceRecord, RiskFlag


def assess_risks(evidence: EvidenceRecord, today: date) -> set[str]:
    flags = set(evidence.risk_flags)
    if not evidence.source_accessible or not evidence.evidence_quote.strip():
        flags.add(RiskFlag.BLOCKED.value)
    if evidence.category == "market" and not all(
        [evidence.geography, evidence.period, evidence.unit, evidence.definition_scope]
    ):
        flags.add(RiskFlag.INCOMPLETE.value)
    age_months = (today.year - evidence.publication_date.year) * 12 + today.month - evidence.publication_date.month
    threshold = 24 if evidence.category in {"market", "supply_chain"} else 12
    if evidence.category not in {"technology", "standard", "history"} and age_months > threshold:
        flags.add(RiskFlag.POSSIBLY_STALE.value)
    return {str(flag) for flag in flags}


def sort_key(evidence: EvidenceRecord) -> tuple[int, str]:
    flags = set(evidence.risk_flags)
    if not evidence.source_accessible or not evidence.evidence_quote.strip() or "blocked" in flags:
        rank = 0
    elif "conflict" in flags:
        rank = 1
    elif "possibly_stale" in flags:
        rank = 2
    elif "incomplete" in flags:
        rank = 3
    else:
        rank = {"needs_edit": 4, "pending": 5, "confirmed": 6, "discarded": 7}[evidence.review_status.value]
    return rank, evidence.id
