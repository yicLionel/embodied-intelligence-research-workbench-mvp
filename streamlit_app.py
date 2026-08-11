from pathlib import Path

import streamlit as st

from src.briefs import build_formal, build_preview, validate_sentence_maps
from src.demo import DIMENSIONS, load_demo_project
from src.domain import ReviewStatus
from src.exporting import evidence_csv, formal_markdown
from src.quality import sort_key
from src.storage import WorkbenchRepository

st.set_page_config(page_title="具身智能研究工作台", layout="wide")
repo = WorkbenchRepository(Path("data") / "workbench.sqlite3")
st.sidebar.title("具身智能研究工作台")
st.sidebar.caption("离线可演示模式：不连接 Dify、Tavily 或 OpenAI。")
page = st.sidebar.radio("研究阶段", ["研究需求", "研究框架", "资料来源", "证据矩阵", "研究简报"], key="nav_task")

if "project_id" not in st.session_state:
    st.session_state.project_id = None
if st.sidebar.button("装载演示研究", key="load_demo"):
    st.session_state.project_id = load_demo_project(repo)
    st.rerun()
pid = st.session_state.project_id

if not pid:
    st.info("尚未创建项目。请在左侧点击“装载演示研究”，以浏览完整离线流程。")

def require_project():
    if not pid:
        st.stop()

if page == "研究需求":
    st.title("01 研究需求")
    st.write("定义研究任务；此离线版本仅使用合成演示资料。")
    if pid:
        project = repo.get_project(pid)
        st.json(project.model_dump())
elif page == "研究框架":
    st.title("02 研究框架")
    require_project()
    questions = repo.list_questions(pid)
    st.caption("七个固定维度。每个保留问题均须批准后，才能进入资料来源。")
    updates=[]
    for question in questions:
        left, right = st.columns([4, 1])
        text = left.text_input(question.dimension, question.text, key=f"text_{question.id}")
        approved = right.checkbox("已批准", question.approved, key=f"approved_{question.id}")
        updates.append(question.model_copy(update={"text": text, "approved": approved}))
    if st.button("保存框架", key="save_framework"):
        repo.save_questions(updates); st.success("已保存框架。")
    ready = all(q.approved and not q.deleted for q in updates) and len({q.dimension for q in updates if not q.deleted}) == len(DIMENSIONS)
    st.button("确认框架并进入资料来源", disabled=not ready, key="confirm_framework")
    if not ready: st.warning("阻塞原因：每个维度至少保留一题，且全部保留问题须标为已批准。")
elif page == "资料来源":
    st.title("03 资料来源")
    require_project()
    st.write("剔除来源会同步把关联证据设为“已剔除”。")
    for source in repo.list_sources(pid):
        cols=st.columns([5,2,2,1])
        cols[0].write(source.title); cols[1].write(source.organization); cols[2].write("可访问" if source.accessible else "不可访问")
        if cols[3].button("剔除", key=f"exclude_{source.id}", disabled=source.excluded): repo.exclude_source(source.id); st.rerun()
elif page == "证据矩阵":
    st.title("04 证据矩阵")
    require_project()
    st.write("风险排序：阻塞、冲突、可能过旧、字段不完整、待修改、待审核、已确认、已剔除。")
    for item in sorted(repo.list_evidence(pid), key=sort_key):
        with st.expander(f"{item.dimension}｜{item.review_status.value}｜{', '.join(item.risk_flags) or 'clean'}"):
            st.write(item.claim); st.caption(f"引用：{item.evidence_quote or '缺少直接引文'}")
            st.caption(f"来源：{item.source_url or item.source_reference or '缺少 reference'}")
            cols=st.columns(3)
            if cols[0].button("确认", key=f"confirm_{item.id}", disabled=not item.can_confirm): repo.set_review_status(item.id, ReviewStatus.CONFIRMED); st.rerun()
            if cols[1].button("待修改", key=f"edit_{item.id}"): repo.set_review_status(item.id, ReviewStatus.NEEDS_EDIT); st.rerun()
            if cols[2].button("剔除", key=f"discard_{item.id}"): repo.set_review_status(item.id, ReviewStatus.DISCARDED); st.rerun()
            if not item.can_confirm: st.warning("阻塞：不可访问、缺少直接引文或缺少引用的记录不能确认。")
else:
    st.title("05 研究简报")
    require_project()
    evidence=repo.list_evidence(pid)
    if st.button("生成候选预览", key="generate_preview"):
        st.session_state.preview=build_preview(evidence)
    if preview:=st.session_state.get("preview"):
        st.warning("待审核、不可导出：预览可能包含未确认的证据。")
        for sentence in preview.sentences: st.write(f"- {sentence.text}")
    if st.button("生成正式简报", key="generate_formal"):
        formal=build_formal(evidence); errors=validate_sentence_maps(formal,evidence)
        if errors: st.error("验证阻断：存在无法映射到已确认的证据。")
        elif not formal.sentences: st.error("验证阻断：尚无可用的已确认事实。")
        else: st.session_state.formal=formal
    if formal:=st.session_state.get("formal"):
        st.success("正式模式：仅使用已确认且可追溯的证据。")
        st.download_button("下载正式 Markdown", formal_markdown(formal), "research-brief.md", key="download_markdown")
        st.download_button("下载证据 CSV", evidence_csv(evidence), "evidence.csv", key="download_csv")
        for sentence in formal.sentences: st.write(f"- {sentence.text}")
