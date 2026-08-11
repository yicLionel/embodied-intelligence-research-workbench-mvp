from src.briefs import build_formal, build_preview, validate_sentence_maps
from src.domain import ReviewStatus
from tests.test_domain import make_evidence


def test_preview_filters_blocked_and_formal_filters_pending():
    clean = make_evidence(id="good")
    blocked = make_evidence(id="bad", source_accessible=False, evidence_quote="")
    assert [x.evidence_id for x in build_preview([clean, blocked]).sentences] == ["good"]
    assert build_formal([clean]).sentences == []
    confirmed = clean.with_status(ReviewStatus.CONFIRMED)
    formal = build_formal([confirmed])
    assert validate_sentence_maps(formal, [confirmed]) == []
