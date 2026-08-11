from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_app_renders_five_stage_navigation():
    app = AppTest.from_file(Path(__file__).parents[1] / "streamlit_app.py").run()
    labels = [item.label for item in app.radio]
    assert "研究阶段" in labels
    assert "离线可演示模式" in " ".join(item.value for item in app.caption)
