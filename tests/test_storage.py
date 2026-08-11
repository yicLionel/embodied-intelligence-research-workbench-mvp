from pathlib import Path

from src.demo import DIMENSIONS, load_demo_project
from src.storage import WorkbenchRepository


def test_reopen_restores_demo_and_excluding_source_discards_evidence(tmp_path: Path):
    db = tmp_path / "workbench.sqlite3"
    repo = WorkbenchRepository(db)
    project_id = load_demo_project(repo)
    assert len(repo.list_questions(project_id)) == 7
    source = repo.list_sources(project_id)[0]
    repo.exclude_source(source.id)
    assert all(item.review_status.value == "discarded" for item in repo.list_evidence(project_id) if item.source_id == source.id)
    reopened = WorkbenchRepository(db)
    assert reopened.get_project(project_id).topic == "具身智能"
    assert len(DIMENSIONS) == 7
