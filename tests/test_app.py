from pathlib import Path

from streamlit.testing.v1 import AppTest


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
