from __future__ import annotations

import streamlit as st

from src.domain import EvidenceRecord, Project, SourceRecord

NAV_LABELS = ["研究需求", "研究框架", "资料来源", "证据矩阵", "研究简报"]
RISK_LABELS = {
    "conflict": "冲突",
    "possibly_stale": "可能过旧",
    "incomplete": "字段不完整",
    "blocked": "阻塞",
    "missing_evidence": "证据不足",
}


def project_metrics(evidence: list[EvidenceRecord], sources: list[SourceRecord]) -> dict[str, int | float]:
    total_sources = len(sources)
    accessible = sum(1 for source in sources if source.accessible and not source.excluded)
    total = len(evidence)
    confirmed = sum(item.review_status.value == "confirmed" for item in evidence)
    needs_edit = sum(item.review_status.value == "needs_edit" for item in evidence)
    pending = sum(item.review_status.value == "pending" for item in evidence)
    discarded = sum(item.review_status.value == "discarded" for item in evidence)
    high_risk = sum(bool(set(item.risk_flags) & set(RISK_LABELS)) or not item.can_confirm for item in evidence)
    return {
        "evidence_total": total,
        "confirmed": confirmed,
        "needs_edit": needs_edit,
        "pending": pending,
        "discarded": discarded,
        "reviewed": confirmed + needs_edit,
        "review_rate": round((confirmed + needs_edit) / total * 100) if total else 0,
        "high_risk": high_risk,
        "source_total": total_sources,
        "source_accessible": accessible,
        "source_access_rate": round(accessible / total_sources * 100) if total_sources else 0,
    }


def risk_breakdown(evidence: list[EvidenceRecord]) -> dict[str, int]:
    result = {label: 0 for label in ("冲突", "可能过旧", "字段不完整", "阻塞")}
    for item in evidence:
        flags = set(item.risk_flags)
        if not item.can_confirm:
            flags.add("blocked")
        for flag, label in RISK_LABELS.items():
            if label in result and flag in flags:
                result[label] += 1
    return result


def inject_terminal_theme() -> None:
    st.markdown(
        """
        <style>
        :root { --navy: #081421; --navy-2: #0f2232; --panel: #11283a; --ink: #edf2f4; --muted: #99abb5; --gold: #c9a96e; --line: rgba(201,169,110,.20); --danger: #dc8b83; --ok: #93c7ad; }
        .stApp { background: radial-gradient(circle at 100% 0%, #17344a 0%, var(--navy) 42%, #06101b 100%); color: var(--ink); }
        [data-testid="stHeader"] { background: rgba(8,20,33,.78); }
        [data-testid="stSidebar"] { background: #091a28; border-right: 1px solid var(--line); }
        [data-testid="stSidebar"] * { color: var(--ink); }
        h1, h2, h3 { letter-spacing: -.02em; color: var(--ink); }
        h1 { font-size: 2.1rem !important; margin-bottom: .2rem; }
        h2 { font-size: 1.35rem !important; }
        .terminal-eyebrow { color: var(--gold); font-size: .72rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; }
        .terminal-subtitle { color: var(--muted); font-size: .9rem; margin-bottom: 1.2rem; }
        .status-strip { display:flex; flex-wrap:wrap; gap: .55rem; padding: .8rem 1rem; margin: .2rem 0 1.2rem; background: rgba(17,40,58,.88); border: 1px solid var(--line); border-radius: 10px; }
        .status-chip { padding: .3rem .65rem; border-radius: 999px; background: rgba(201,169,110,.10); color: var(--ink); border: 1px solid rgba(201,169,110,.22); font-size: .78rem; }
        .status-chip strong { color: var(--gold); margin-right: .25rem; }
        .kpi-card { background: linear-gradient(145deg, rgba(17,40,58,.96), rgba(12,29,44,.96)); border: 1px solid var(--line); border-radius: 10px; padding: .82rem .95rem; min-height: 98px; }
        .kpi-label { color: var(--muted); font-size: .74rem; letter-spacing: .05em; }
        .kpi-value { color: var(--ink); font-size: 1.65rem; font-weight: 700; line-height: 1.25; margin-top: .28rem; }
        .kpi-note { color: var(--muted); font-size: .72rem; margin-top: .18rem; }
        .terminal-panel { background: rgba(17,40,58,.72); border: 1px solid var(--line); border-radius: 10px; padding: 1rem 1.1rem; margin: .7rem 0; }
        .panel-title { color: var(--gold); font-size: .78rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; margin-bottom: .6rem; }
        .metric-line { display:flex; justify-content:space-between; gap: 1rem; padding: .45rem 0; border-bottom: 1px solid rgba(153,171,181,.12); color: var(--muted); }
        .metric-line:last-child { border-bottom: 0; }
        .metric-line strong { color: var(--ink); }
        .risk-pill { display:inline-block; padding:.2rem .5rem; margin:.12rem .2rem .12rem 0; border-radius:999px; background:rgba(220,139,131,.12); color:#f1b0a7; border:1px solid rgba(220,139,131,.28); font-size:.74rem; }
        .success-pill { background:rgba(147,199,173,.12); color:#b4dfc7; border-color:rgba(147,199,173,.28); }
        div[data-testid="stMetric"] { background: rgba(17,40,58,.68); border: 1px solid var(--line); border-radius: 10px; padding: .75rem; }
        div[data-testid="stMetricLabel"] { color: var(--muted); }
        div[data-testid="stMetricValue"] { color: var(--ink); }
        .stButton > button { border-radius: 7px; border: 1px solid rgba(201,169,110,.4); background: rgba(201,169,110,.10); color: var(--ink); }
        .stButton > button:hover { border-color: var(--gold); color: var(--gold); }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_terminal_header(project: Project | None, current_page: str, metrics: dict[str, int | float]) -> None:
    if not project:
        return
    st.markdown('<div class="terminal-eyebrow">Investment Research Workbench / Offline Desk</div>', unsafe_allow_html=True)
    st.title(project.topic)
    st.markdown('<div class="terminal-subtitle">中国主视角 · 全球技术对照 · 证据优先研究底稿</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="status-strip"><span class="status-chip"><strong>当前阶段</strong>{current_page}</span><span class="status-chip"><strong>范围</strong>{project.geography}</span><span class="status-chip"><strong>模式</strong>离线可演示</span><span class="status-chip"><strong>审核进度</strong>{metrics["reviewed"]}/{metrics["evidence_total"]} 条</span><span class="status-chip"><strong>高风险</strong>{metrics["high_risk"]} 条</span></div>',
        unsafe_allow_html=True,
    )


def render_kpi_row(metrics: dict[str, int | float]) -> None:
    columns = st.columns(5)
    cards = [
        ("证据总数", metrics["evidence_total"], "结构化记录"),
        ("审核进度", f'{metrics["review_rate"]}%', f'{metrics["reviewed"]} 条已处理'),
        ("已确认", metrics["confirmed"], "可进入正式简报"),
        ("高风险", metrics["high_risk"], "优先人工复核"),
        ("来源可访问率", f'{metrics["source_access_rate"]}%', f'{metrics["source_accessible"]}/{metrics["source_total"]} 个来源'),
    ]
    for column, (label, value, note) in zip(columns, cards):
        column.markdown(f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>', unsafe_allow_html=True)


def render_panel_title(label: str, caption: str | None = None) -> None:
    st.markdown(f'<div class="panel-title">{label}</div>', unsafe_allow_html=True)
    if caption:
        st.caption(caption)
