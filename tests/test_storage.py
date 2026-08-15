from pathlib import Path

from src.demo import DIMENSIONS, load_demo_project
from src.online_research import create_online_project
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


def test_list_projects_returns_all_projects_in_creation_order(tmp_path: Path):
    repo = WorkbenchRepository(tmp_path / "list.sqlite3")
    demo_id = load_demo_project(repo)
    online_id = create_online_project(repo, "物流机器人", "中国", "2025–2026", "内部讨论")
    projects = repo.list_projects()
    assert [p.id for p in projects] == [demo_id, online_id]
    assert projects[1].topic == "物流机器人"
    assert projects[1].id.startswith("online-")
