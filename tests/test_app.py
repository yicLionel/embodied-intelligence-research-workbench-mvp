from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.storage import WorkbenchRepository


def test_app_renders_five_stage_navigation():
    app = AppTest.from_file(Path(__file__).parents[1] / "streamlit_app.py").run()
    labels = [item.label for item in app.radio]
    assert "研究阶段" in labels
    assert "离线可演示模式" in " ".join(item.value for item in app.caption)


def test_demo_dashboard_shows_terminal_status_and_kpis():
    app = AppTest.from_file(Path(__file__).parents[1] / "streamlit_app.py").run()
    app.button[0].click().run()
    visible = " ".join(item.value for item in app.markdown)
    assert "项目状态" in visible
    assert "审核进度" in visible
    assert "研究范围" in visible
    assert "七维框架覆盖" in visible


def test_terminal_pages_expose_risk_and_brief_surfaces():
    app = AppTest.from_file(Path(__file__).parents[1] / "streamlit_app.py").run()
    app.button[0].click().run()
    app.radio[0].set_value("证据矩阵").run()
    evidence_text = " ".join(item.value for item in app.markdown)
    assert "风险队列" in evidence_text
    assert "来源可访问率" in evidence_text
    app.radio[0].set_value("研究简报").run()
    brief_text = " ".join(item.value for item in app.markdown)
    assert "候选预览" in brief_text
    assert "正式简报" in brief_text
    assert "不可导出" in brief_text


def test_online_project_framework_includes_custom_questions_and_gate():
    app = AppTest.from_file(Path(__file__).parents[1] / "streamlit_app.py").run()
    app.text_input(key="online_topic").set_value("具身智能")
    app.text_area(key="online_focus_questions").set_value("代表性团队：有哪些代表性创业团队？\n重点关注商业化订单")
    submit = next(button for button in app.button if button.label == "创建并进入研究框架")
    submit.click().run()
    app.radio[0].set_value("研究框架").run()
    visible = " ".join(item.value for item in app.markdown)
    assert "代表性团队" in visible, "自定义维度应出现在研究框架页"
    assert "自定义问题" in visible, "纯问题应归入自定义问题维度"
    for box in app.checkbox:
        if "已批准" in box.label:
            box.check()
    app.run()
    app.button(key="save_framework").click().run()
    assert "框架已保存" in " ".join(item.value for item in app.success)
    assert not app.button(key="confirm_framework").disabled, "全部批准后确认按钮应可用"


def test_framework_one_click_approve_all_questions(monkeypatch, tmp_path):
    monkeypatch.setenv("APP_DB_PATH", str(tmp_path / "approve.sqlite3"))
    app = AppTest.from_file(Path(__file__).parents[1] / "streamlit_app.py").run()
    app.button(key="load_demo").click().run()
    app.radio[0].set_value("研究框架").run()
    approve_boxes = [box for box in app.checkbox if "已批准" in box.label]
    assert len(approve_boxes) == 7 and not any(box.value for box in approve_boxes)
    app.button(key="approve_all_questions").click().run()
    approve_boxes = [box for box in app.checkbox if "已批准" in box.label]
    assert all(box.value for box in approve_boxes), "一键批准后全部问题应为已批准"
    app.button(key="save_framework").click().run()
    assert "框架已保存" in " ".join(item.value for item in app.success)
    assert not app.button(key="confirm_framework").disabled, "一键批准后确认按钮应可用"


def test_evidence_one_click_confirm_all_qualifying(monkeypatch, tmp_path):
    monkeypatch.setenv("APP_DB_PATH", str(tmp_path / "confirm.sqlite3"))
    app = AppTest.from_file(Path(__file__).parents[1] / "streamlit_app.py").run()
    app.button(key="load_demo").click().run()
    app.radio[0].set_value("证据矩阵").run()
    btn = app.button(key="confirm_all_evidence")
    assert "一键确认 6 条合格证据" in btn.label, "演示项目应有 6 条可确认的 pending 证据"
    btn.click().run()
    assert app.button(key="confirm_all_evidence").disabled, "全部确认后一键按钮应禁用"
    repo = WorkbenchRepository(Path(tmp_path / "confirm.sqlite3"))
    statuses = {item.id: item.review_status.value for item in repo.list_evidence("demo-embodied-intelligence")}
    assert sum(v == "confirmed" for v in statuses.values()) == 6
    assert statuses["e-5"] == "pending", "阻塞证据不应被一键确认"
