from src.briefs import build_formal
from src.domain import ReviewStatus
from src.exporting import evidence_csv, formal_markdown
from tests.test_domain import make_evidence


def test_csv_keeps_status_and_risks():
    evidence = make_evidence(risk_flags=["conflict"]).with_status(ReviewStatus.CONFIRMED)
    assert "review_status" in evidence_csv([evidence]).decode()
    assert "正式研究简报" in formal_markdown(build_formal([evidence]))
