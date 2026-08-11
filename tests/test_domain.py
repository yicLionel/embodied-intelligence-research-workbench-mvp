from datetime import date

from src.domain import EvidenceRecord, ReviewStatus


def make_evidence(**changes):
    data = {
        "id": "ev-1", "project_id": "pr-1", "question_id": "q-1", "dimension": "融资活动与商业化进展",
        "claim": "某公司完成融资", "source_id": "s-1", "source_title": "示例", "source_url": "https://example.com",
        "source_reference": None, "source_accessible": True, "publication_date": date(2026, 1, 1),
        "evidence_quote": "公司公告确认完成融资。", "geography": "中国", "period": "2026", "unit": None,
        "definition_scope": "具身智能", "category": "commercialization", "risk_flags": [], "review_status": "pending",
    }
    data.update(changes)
    return EvidenceRecord.model_validate(data)


def test_invalid_evidence_cannot_be_confirmed():
    evidence = make_evidence(source_accessible=False, evidence_quote="", source_url=None)
    assert not evidence.can_confirm
    assert evidence.with_status(ReviewStatus.CONFIRMED).review_status is ReviewStatus.PENDING
