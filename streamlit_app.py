from pathlib import Path

import streamlit as st

from src.briefs import build_formal, build_preview, validate_sentence_maps
from src.demo import DIMENSIONS, load_demo_project
from src.domain import ReviewStatus
from src.exporting import evidence_csv, formal_markdown
from src.quality import sort_key
from src.storage import WorkbenchRepository
from src.ui import (
    NAV_LABELS,
    inject_terminal_theme,
    project_metrics,
    render_kpi_row,
    render_panel_title,
    render_terminal_header,
    risk_breakdown,
)

st.set_page_config(page_title="具身智能研究终端", page_icon="◈", layout="wide", initial_sidebar_state="expanded")
inject_terminal_theme()
repo = WorkbenchRepository(Path("data") / "workbench.sqlite3")

st.sidebar.markdown('<div class="terminal-eyebrow">Research Desk / 01</div>', unsafe_allow_html=True)
st.sidebar.markdown("## 具身智能研究终端")
st.sidebar.caption("证据优先工作流 · 离线可演示模式")
page = st.sidebar.radio("研究阶段", NAV_LABELS, key="nav_task")
st.sidebar.markdown("---")
if st.sidebar.button("装载演示研究", key="load_demo"):
    st.session_state.project_id = load_demo_project(repo)
    st.session_state.pop("preview", None)
    st.session_state.pop("formal", None)
    st.rerun()

if "project_id" not in st.session_state:
    st.session_state.project_id = None
pid = st.session_state.project_id
project = repo.get_project(pid) if pid else None
evidence = repo.list_evidence(pid) if pid else []
sources = repo.list_sources(pid) if pid else []
metrics = project_metrics(evidence, sources) if project else None

if project and metrics:
    render_terminal_header(project, page, metrics)
    st.sidebar.markdown("### 阶段导航")
    current_index = NAV_LABELS.index(page)
    for index, label in enumerate(NAV_LABELS):
        marker = "●" if index == current_index else ("✓" if index < current_index else "○")
        st.sidebar.markdown(f"`{marker}`  {index + 1:02d}  {label}")
    st.sidebar.markdown("---")
    st.sidebar.caption(f"项目 ID  /  {project.id}")
else:
    st.sidebar.info("尚未载入项目。点击上方按钮进入离线演示。")


def no_project() -> None:
    st.markdown('<div class="terminal-eyebrow">Investment Research Workbench</div>', unsafe_allow_html=True)
    st.title("具身智能研究终端")
    st.markdown('<div class="terminal-subtitle">把研究范围、来源、证据和简报放在同一条可审计链路上。</div>', unsafe_allow_html=True)
    st.markdown("### 开始一份研究底稿")
    st.info("当前是离线可演示模式。载入演示研究后，你可以浏览五个阶段、风险队列和审核门禁；演示来源为合成数据。")
    cols = st.columns(3)
    for column, title, copy in zip(cols, ["01 先定范围", "02 再审证据", "03 最后成稿"], ["固定七维框架，避免研究范围漂移。", "按风险优先级查看引用、口径和状态。", "只有已确认事实可以进入正式简报。"]):
        column.markdown(f'<div class="terminal-panel"><div class="panel-title">{title}</div><div>{copy}</div></div>', unsafe_allow_html=True)
    st.markdown("### 研究阶段")
    st.caption("研究需求 → 研究框架 → 资料来源 → 证据矩阵 → 研究简报")


if not project:
    no_project()
elif page == "研究需求":
    st.markdown('<div class="terminal-eyebrow">01 / Scoping Console</div>', unsafe_allow_html=True)
    st.title("研究需求")
    st.markdown('<div class="terminal-subtitle">先确定项目范围，再让证据进入审核队列。</div>', unsafe_allow_html=True)
    render_kpi_row(metrics)
    left, right = st.columns([1.35, 1])
    with left:
        st.markdown("### 项目状态")
        st.markdown('<div class="terminal-panel">', unsafe_allow_html=True)
        render_panel_title("研究范围")
        st.markdown(f'<div class="metric-line"><span>主题</span><strong>{project.topic}</strong></div><div class="metric-line"><span>地域口径</span><strong>{project.geography}</strong></div><div class="metric-line"><span>时间范围</span><strong>{project.time_range}</strong></div><div class="metric-line"><span>研究用途</span><strong>{project.purpose}</strong></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("### 七维框架覆盖")
        questions = repo.list_questions(pid)
        for dimension in DIMENSIONS:
            count = sum(q.dimension == dimension and not q.deleted for q in questions)
            status = "已覆盖" if count else "待补充"
            st.markdown(f'<div class="metric-line"><span>{dimension}</span><strong>{count} 个问题 · {status}</strong></div>', unsafe_allow_html=True)
    with right:
        st.markdown("### 风险概览")
        st.markdown('<div class="terminal-panel">', unsafe_allow_html=True)
        for label, count in risk_breakdown(evidence).items():
            pill = "risk-pill" if count else "risk-pill success-pill"
            st.markdown(f'<span class="{pill}">{label} {count}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("### 下一步")
        if metrics["confirmed"]:
            st.success("已有已确认事实，可以进入研究简报复核。")
        else:
            st.warning("先进入“研究框架”，批准七维问题后再复核来源和证据。")
elif page == "研究框架":
    st.markdown('<div class="terminal-eyebrow">02 / Framework Review</div>', unsafe_allow_html=True)
    st.title("研究框架")
    st.markdown('<div class="terminal-subtitle">研究框架是第一个人工检查点：未全部批准前，不进入采集。</div>', unsafe_allow_html=True)
    render_kpi_row(metrics)
    questions = repo.list_questions(pid)
    approved = sum(q.approved and not q.deleted for q in questions)
    st.markdown(f"### 七维框架覆盖　`{approved}/{len(questions)}` 个问题已批准")
    updates = []
    for question in questions:
        with st.container(border=True):
            left, middle, right = st.columns([4, 1, 1])
            left.markdown(f"**{question.dimension}**")
            text = left.text_input("研究问题", question.text, key=f"text_{question.id}", label_visibility="collapsed")
            priority = middle.selectbox("优先级", [1, 2, 3], index=question.priority - 1, key=f"priority_{question.id}")
            approved_value = right.checkbox("已批准", question.approved, key=f"approved_{question.id}")
            updates.append(question.model_copy(update={"text": text, "priority": priority, "approved": approved_value}))
    action_left, action_right = st.columns([1, 2])
    if action_left.button("保存框架", key="save_framework"):
        repo.save_questions(updates)
        st.success("框架已保存，审核事件已保留在本地项目中。")
    ready = all(q.approved and not q.deleted for q in updates) and len({q.dimension for q in updates if not q.deleted}) == len(DIMENSIONS)
    action_right.button("确认框架并进入资料来源", disabled=not ready, key="confirm_framework")
    if not ready:
        st.warning("确认阻断：每个维度至少保留一题，且全部保留问题须标为已批准。")
    else:
        st.success("框架已满足进入资料来源的门禁条件。")
elif page == "资料来源":
    st.markdown('<div class="terminal-eyebrow">03 / Source Room</div>', unsafe_allow_html=True)
    st.title("资料来源")
    st.markdown('<div class="terminal-subtitle">先看来源角色与可访问性，再决定哪些材料值得进入证据矩阵。</div>', unsafe_allow_html=True)
    render_kpi_row(metrics)
    st.markdown(f"### 来源可访问率　`{metrics['source_access_rate']}%`")
    access_filter = st.selectbox("访问状态", ["全部来源", "仅可访问", "仅不可访问"], key="source_access_filter")
    role_filter = st.selectbox("来源角色", ["全部角色"] + sorted({source.source_role for source in sources}), key="source_role_filter")
    visible_sources = [source for source in sources if (access_filter == "全部来源" or (access_filter == "仅可访问" and source.accessible) or (access_filter == "仅不可访问" and not source.accessible)) and (role_filter == "全部角色" or source.source_role == role_filter)]
    st.caption(f"当前显示 {len(visible_sources)} / {len(sources)} 个来源。剔除来源会同步将关联证据标记为已剔除。")
    for source in visible_sources:
        with st.container(border=True):
            columns = st.columns([4, 1.5, 1.2, 1.2, .8])
            columns[0].markdown(f"**{source.title}**  \n{source.organization}")
            columns[1].caption(f"角色 · {source.source_role}")
            columns[2].caption(f"日期 · {source.publication_date}")
            columns[3].markdown("<span class='success-pill'>可访问</span>" if source.accessible else "<span class='risk-pill'>不可访问</span>", unsafe_allow_html=True)
            if columns[4].button("剔除", key=f"exclude_{source.id}", disabled=source.excluded):
                repo.exclude_source(source.id)
                st.rerun()
elif page == "证据矩阵":
    st.markdown('<div class="terminal-eyebrow">04 / Evidence Ledger</div>', unsafe_allow_html=True)
    st.title("证据矩阵")
    st.markdown('<div class="terminal-subtitle">默认按风险优先级排列，把人工时间留给最需要判断的记录。</div>', unsafe_allow_html=True)
    render_kpi_row(metrics)
    st.markdown("### 风险队列")
    risk_counts = risk_breakdown(evidence)
    st.markdown(" ".join(f"<span class='risk-pill'>{label} {count}</span>" for label, count in risk_counts.items()), unsafe_allow_html=True)
    status_filter = st.selectbox("审核状态", ["全部状态", "pending", "needs_edit", "confirmed", "discarded"], key="evidence_status_filter")
    risk_filter = st.selectbox("风险筛选", ["全部风险", "冲突", "可能过旧", "字段不完整", "阻塞"], key="evidence_risk_filter")
    risk_value = {label: flag for flag, label in {"conflict": "冲突", "possibly_stale": "可能过旧", "incomplete": "字段不完整", "blocked": "阻塞"}.items()}
    filtered = []
    for item in sorted(evidence, key=sort_key):
        status_match = status_filter == "全部状态" or item.review_status.value == status_filter
        risk_match = risk_filter == "全部风险" or risk_value[risk_filter] in item.risk_flags or (risk_filter == "阻塞" and not item.can_confirm)
        if status_match and risk_match:
            filtered.append(item)
    st.caption(f"风险优先队列 · 显示 {len(filtered)} / {len(evidence)} 条记录。")
    for item in filtered:
        risk_text = ", ".join(item.risk_flags) or "clean"
        with st.expander(f"{item.dimension}  ·  {item.review_status.value}  ·  {risk_text}"):
            st.markdown(f"### {item.claim}")
            cols = st.columns([1.3, 1, 1])
            cols[0].caption(f"地域 / {item.geography or '缺失'}\n\n时期 / {item.period or '缺失'}")
            cols[1].caption(f"单位 / {item.unit or '缺失'}\n\n口径 / {item.definition_scope or '缺失'}")
            cols[2].caption(f"来源 / {item.source_title}\n\n日期 / {item.publication_date}")
            st.markdown(f"**直接引文**  \n> {item.evidence_quote or '缺少直接引文'}")
            st.caption(f"引用 / {item.source_url or item.source_reference or '缺少 URL 或本地 reference'}")
            action_cols = st.columns(3)
            if action_cols[0].button("确认", key=f"confirm_{item.id}", disabled=not item.can_confirm):
                repo.set_review_status(item.id, ReviewStatus.CONFIRMED)
                st.rerun()
            if action_cols[1].button("待修改", key=f"edit_{item.id}"):
                repo.set_review_status(item.id, ReviewStatus.NEEDS_EDIT)
                st.rerun()
            if action_cols[2].button("剔除", key=f"discard_{item.id}"):
                repo.set_review_status(item.id, ReviewStatus.DISCARDED)
                st.rerun()
            if not item.can_confirm:
                st.warning("确认阻断：不可访问、缺少直接引文或缺少引用的记录不能确认。")
elif page == "研究简报":
    st.markdown('<div class="terminal-eyebrow">05 / Brief Room</div>', unsafe_allow_html=True)
    st.title("研究简报")
    st.markdown('<div class="terminal-subtitle">候选预览帮助你先看结构；正式简报只接受已确认、可追溯的事实。</div>', unsafe_allow_html=True)
    render_kpi_row(metrics)
    preview = build_preview(evidence)
    formal_candidate = build_formal(evidence)
    validation_errors = validate_sentence_maps(formal_candidate, evidence)
    left, right = st.columns(2)
    with left:
        st.markdown("### 候选预览")
        st.markdown('<div class="terminal-panel"><div class="panel-title">Candidate Preview · 待审核 · 不可导出</div><div>可访问、有直接引文的候选事实，仍可能包含未确认记录。</div></div>', unsafe_allow_html=True)
        st.metric("候选事实", len(preview.sentences))
        if st.button("生成候选预览", key="generate_preview"):
            st.session_state.preview = preview
        active_preview = st.session_state.get("preview")
        if active_preview:
            st.warning("待审核、不可导出：逐条回查引用后，再在证据矩阵中确认。")
            for sentence in active_preview.sentences:
                st.write(f"- {sentence.text}")
    with right:
        st.markdown("### 正式简报")
        formal_status = "可生成" if formal_candidate.sentences and not validation_errors else "验证阻断"
        st.markdown(f'<div class="terminal-panel"><div class="panel-title">Formal Brief · {formal_status}</div><div>仅使用 review_status = confirmed 的证据，逐句映射通过后才可导出。</div></div>', unsafe_allow_html=True)
        st.metric("已确认事实", len(formal_candidate.sentences))
        if st.button("生成正式简报", key="generate_formal"):
            if validation_errors:
                st.error("验证阻断：存在无法映射到已确认证据的句子。")
            elif not formal_candidate.sentences:
                st.error("验证阻断：尚无可用的已确认事实。")
            else:
                st.session_state.formal = formal_candidate
        active_formal = st.session_state.get("formal")
        if active_formal:
            st.success("正式模式：仅使用已确认且可追溯的证据。")
            st.download_button("下载正式 Markdown", formal_markdown(active_formal), "research-brief.md", key="download_markdown")
            st.download_button("下载证据 CSV", evidence_csv(evidence), "evidence.csv", key="download_csv")
            for sentence in active_formal.sentences:
                st.write(f"- {sentence.text}")
