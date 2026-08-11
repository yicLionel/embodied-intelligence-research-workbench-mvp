from datetime import date

from src.quality import assess_risks, sort_key
from tests.test_domain import make_evidence


def test_quality_flags_stale_and_incomplete_market_record():
    evidence = make_evidence(category="market", publication_date=date(2024, 7, 1), geography=None, period=None, unit=None, definition_scope=None)
    flags = assess_risks(evidence, date(2026, 8, 12))
    assert {"possibly_stale", "incomplete"}.issubset(flags)


def test_blocked_evidence_sorts_before_conflict():
    blocked = make_evidence(source_accessible=False)
    conflict = make_evidence(risk_flags=["conflict"])
    assert sort_key(blocked) < sort_key(conflict)
