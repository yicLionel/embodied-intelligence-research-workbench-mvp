import json
from datetime import date

import httpx

from src import online_research
from src.demo import DIMENSIONS
from src.online_research import (
    DifyWorkflowClient,
    OnlineResearchConfig,
    SearchHit,
    canonical_url,
    create_online_project,
    generate_queries,
    parse_workflow_output,
    run_online_research,
)
from src.storage import WorkbenchRepository


def test_generate_queries_returns_bilingual_queries_per_question():
    queries = generate_queries("具身智能", "中国", "2024–2026", "市场规模与 CAGR")
    assert len(queries) == 3
    assert any("具身智能" in query for query in queries)
    assert any("embodied" in query.lower() for query in queries)


def test_canonical_url_removes_tracking_and_trailing_slash():
    assert canonical_url("https://example.com/report/?utm_source=x#page=2") == "https://example.com/report"


def test_dify_workflow_client_sends_blocking_run_request():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"workflow_run_id": "run-1", "data": {"status": "succeeded", "outputs": {"result": "{}"}}})

    client = DifyWorkflowClient(
        base_url="https://dify.example/v1",
        api_key="secret",
        transport=httpx.MockTransport(handler),
    )
    result = client.run({"topic": "具身智能"}, user="UT-01")
    assert result.run_id == "run-1"
    assert seen["url"].endswith("/workflows/run")
    assert seen["auth"] == "Bearer secret"
    assert seen["body"]["response_mode"] == "blocking"


def test_parse_workflow_output_accepts_json_string_output():
    payload = parse_workflow_output({"result": '{"evidence": [{"claim": "x"}]}'})
    assert payload["evidence"][0]["claim"] == "x"


def test_online_config_reports_missing_provider_keys():
    config = OnlineResearchConfig()
    assert config.missing_keys == ["TAVILY_API_KEY"]
    assert config.optional_missing_keys == ["DIFY_EVIDENCE_API_KEY", "DIFY_BRIEF_API_KEY"]


def test_online_config_uses_safe_timeout_when_environment_value_is_invalid(monkeypatch):
    monkeypatch.setenv("ONLINE_RESEARCH_TIMEOUT", "not-a-number")
    assert OnlineResearchConfig.from_env().timeout_seconds == 60.0


def test_create_online_project_persists_user_scope_and_fixed_framework(tmp_path):
    repo = WorkbenchRepository(tmp_path / "online.sqlite3")
    project_id = create_online_project(repo, "物流机器人", "中国", "2025–2026", "内部讨论", "关注订单")
    project = repo.get_project(project_id)
    questions = repo.list_questions(project_id)
    assert project.topic == "物流机器人"
    assert project.focus_questions == "关注订单"
    assert [question.dimension for question in questions] == DIMENSIONS
    assert not any(question.approved for question in questions)


def test_run_online_research_persists_deduped_sources_and_each_dimension_evidence(tmp_path, monkeypatch):
    repo = WorkbenchRepository(tmp_path / "online.sqlite3")
    project_id = create_online_project(repo, "物流机器人", "中国", "2025–2026", "内部讨论")
    questions = [question.model_copy(update={"approved": True}) for question in repo.list_questions(project_id)]
    repo.save_questions(questions)

    class FakeTavilyClient:
        def __init__(self, api_key, timeout):
            assert api_key == "tv-test"

        def search(self, query):
            return [SearchHit("行业研究报告", "https://example.com/report?utm_source=test", "报告原文摘录。", date(2026, 1, 1))]

    monkeypatch.setattr(online_research, "TavilyClient", FakeTavilyClient)
    result = run_online_research(repo, project_id, OnlineResearchConfig(tavily_api_key="tv-test"))

    assert result.status == "succeeded"
    assert result.source_count == 1
    assert result.evidence_count == 7
    assert len(repo.list_sources(project_id)) == 1
    assert len(repo.list_evidence(project_id)) == 7
    assert all(item.review_status.value == "pending" for item in repo.list_evidence(project_id))
