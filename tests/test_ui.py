from datetime import date

from src.domain import EvidenceRecord, SourceRecord
from src.ui import project_metrics, risk_breakdown


def evidence(status="pending", risks=None, accessible=True):
    return EvidenceRecord(
        id=f"e-{status}-{accessible}", project_id="p", question_id="q", dimension="市场定义与边界",
        claim="演示结论", source_id="s", source_title="演示来源", source_url="https://example.com",
        source_accessible=accessible, publication_date=date(2026, 1, 1), evidence_quote="直接原文摘录",
        geography="中国", period="2026", definition_scope="具身智能", category="market",
        risk_flags=risks or [], review_status=status,
    )


def test_project_metrics_counts_review_progress_and_access_rate():
    records = [evidence("pending"), evidence("confirmed"), evidence("needs_edit", ["conflict"]), evidence("discarded", ["blocked"], False)]
    sources = [SourceRecord(id="s1", project_id="p", title="一", organization="机构", source_role="research", publication_date=date(2026, 1, 1), url="https://a", accessible=True), SourceRecord(id="s2", project_id="p", title="二", organization="机构", source_role="lead", publication_date=date(2026, 1, 1), url="https://b", accessible=False)]
    metrics = project_metrics(records, sources)
    assert metrics["evidence_total"] == 4
    assert metrics["confirmed"] == 1
    assert metrics["reviewed"] == 2
    assert metrics["source_access_rate"] == 50


def test_risk_breakdown_uses_visible_chinese_buckets():
    result = risk_breakdown([evidence("pending", ["conflict"]), evidence("pending", ["possibly_stale"]), evidence("pending", ["incomplete"])])
    assert result == {"冲突": 1, "可能过旧": 1, "字段不完整": 1, "阻塞": 0}
