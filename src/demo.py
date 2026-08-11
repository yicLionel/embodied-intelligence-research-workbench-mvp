from datetime import date

from src.domain import EvidenceRecord, Project, ResearchQuestion, SourceRecord

DIMENSIONS = ["市场定义与边界", "市场规模与 CAGR", "产业链与关键环节", "竞争格局与标杆公司", "技术趋势与能力演进", "融资活动与商业化进展", "风险、争议与关键假设"]

def load_demo_project(repo) -> str:
    pid="demo-embodied-intelligence"
    repo.save_project(Project(id=pid))
    repo.save_questions([ResearchQuestion(id=f"q-{n}",project_id=pid,dimension=d,text=f"{d}的核心问题是什么？",priority=2) for n,d in enumerate(DIMENSIONS,1)])
    sources=[SourceRecord(id="s-clean",project_id=pid,title="离线演示：产业进展",organization="示例研究机构",source_role="research",publication_date=date(2026,6,1),url="https://example.com/demo"),SourceRecord(id="s-old",project_id=pid,title="离线演示：历史融资",organization="示例媒体",source_role="media",publication_date=date(2025,1,1),url="https://example.com/old"),SourceRecord(id="s-blocked",project_id=pid,title="离线演示：不可访问",organization="示例",source_role="lead",publication_date=date(2026,1,1),url="https://example.com/blocked",accessible=False)]
    repo.save_sources(sources)
    flags=[[],["conflict"],["possibly_stale"],["incomplete"],["blocked"],[],[]]
    evidence=[]
    for n,d in enumerate(DIMENSIONS,1):
        source="s-blocked" if n==5 else ("s-old" if n==6 else "s-clean")
        evidence.append(EvidenceRecord(id=f"e-{n}",project_id=pid,question_id=f"q-{n}",dimension=d,claim=f"离线演示：{d}存在可审核研究发现。",source_id=source,source_title="离线演示来源",source_url="https://example.com/demo" if source!="s-blocked" else None,source_accessible=source!="s-blocked",publication_date=date(2025,1,1) if source=="s-old" else date(2026,6,1),evidence_quote="这是直接支持该离线演示结论的原文摘录。" if source!="s-blocked" else "",geography="中国",period="2026",unit="亿元" if n==2 else None,definition_scope="具身智能",category="market" if n in {2,3} else "commercialization",risk_flags=flags[n-1]))
    repo.save_evidence(evidence)
    return pid
