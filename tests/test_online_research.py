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
    project_id = create_online_project(repo, "物流机器人", "中国", "2025–2026", "内部讨论")
    project = repo.get_project(project_id)
    questions = repo.list_questions(project_id)
    assert project.topic == "物流机器人"
    assert [question.dimension for question in questions] == DIMENSIONS
    assert not any(question.approved for question in questions)


def test_parse_custom_questions_supports_dimension_prefix():
    from src.online_research import _parse_custom_questions
    pairs = _parse_custom_questions("代表性团队：具身智能领域有哪些代表性创业团队？\n重点关注商业化订单\n\n")
    assert pairs == [
        ("代表性团队", "具身智能领域有哪些代表性创业团队？"),
        ("自定义问题", "重点关注商业化订单"),
    ]


def test_create_online_project_appends_custom_questions_after_framework(tmp_path):
    repo = WorkbenchRepository(tmp_path / "online.sqlite3")
    focus = "代表性团队：具身智能领域有哪些代表性创业团队？\n重点关注商业化订单"
    project_id = create_online_project(repo, "具身智能", "中国", "2024–2026", "内部讨论", focus)
    questions = repo.list_questions(project_id)
    assert len(questions) == len(DIMENSIONS) + 2
    assert [q.dimension for q in questions[: len(DIMENSIONS)]] == DIMENSIONS
    assert questions[len(DIMENSIONS)].dimension == "代表性团队"
    assert "代表性创业团队" in questions[len(DIMENSIONS)].text
    assert questions[len(DIMENSIONS) + 1].dimension == "自定义问题"
    assert "商业化订单" in questions[len(DIMENSIONS) + 1].text
    assert not any(question.approved for question in questions)


def test_run_online_research_generates_evidence_for_custom_questions(tmp_path, monkeypatch):
    repo = WorkbenchRepository(tmp_path / "online.sqlite3")
    project_id = create_online_project(repo, "具身智能", "中国", "2024–2026", "内部讨论", "代表性团队：有哪些代表团队？")
    questions = [question.model_copy(update={"approved": True}) for question in repo.list_questions(project_id)]
    repo.save_questions(questions)

    class FakeTavilyClient:
        def __init__(self, api_key, timeout):
            assert api_key == "tv-test"

        def search(self, query):
            return [SearchHit("团队盘点", "https://example.com/team", "代表团队原文摘录。", date(2026, 1, 1))]

    monkeypatch.setattr(online_research, "TavilyClient", FakeTavilyClient)
    result = run_online_research(repo, project_id, OnlineResearchConfig(tavily_api_key="tv-test"))

    assert result.status == "succeeded"
    assert result.evidence_count == len(DIMENSIONS) + 1
    evidence = repo.list_evidence(project_id)
    assert any(item.dimension == "代表性团队" for item in evidence)
    assert all(item.review_status.value == "pending" for item in evidence)


def test_fallback_evidence_cleans_markdown_and_html_noise(tmp_path, monkeypatch):
    from src.online_research import _clean_quote
    noisy = "[![Image 1](https://x.com/a.png)](javascript:void(0)) <div>市场增速 35%</div> ![](/uploads/x.png) [正文链接](https://x.com/doc)"
    cleaned = _clean_quote(noisy)
    assert "![Image 1]" not in cleaned and "<div>" not in cleaned and "javascript" not in cleaned
    assert "市场增速 35%" in cleaned
    assert "正文链接" in cleaned

    repo = WorkbenchRepository(tmp_path / "online.sqlite3")
    project_id = create_online_project(repo, "具身智能", "中国", "2024–2026", "内部讨论")
    questions = [q.model_copy(update={"approved": True}) for q in repo.list_questions(project_id)]
    repo.save_questions(questions)

    class NoisyTavily:
        def __init__(self, api_key, timeout):
            pass

        def search(self, query):
            return [SearchHit("行业报告", "https://example.com/r", "干净摘录：市场 35%。", date(2026, 1, 1), raw_content="[![图](https://x.png)](javascript:void(0)) 噪声正文")]

    monkeypatch.setattr(online_research, "TavilyClient", NoisyTavily)
    result = run_online_research(repo, project_id, OnlineResearchConfig(tavily_api_key="tv-test"))
    evidence = repo.list_evidence(project_id)
    assert result.evidence_count == len(DIMENSIONS)
    assert all("![Image" not in (item.evidence_quote or "") and "javascript" not in (item.evidence_quote or "") for item in evidence)


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


def test_run_online_research_wraps_dify_array_inputs_in_items_object(tmp_path, monkeypatch):
    """Dify json_object 输入只接受对象：questions/sources 必须包成 {"items": [...]}。"""
    repo = WorkbenchRepository(tmp_path / "online.sqlite3")
    project_id = create_online_project(repo, "具身智能", "中国", "2024–2026", "内部讨论")
    questions = [question.model_copy(update={"approved": True}) for question in repo.list_questions(project_id)]
    repo.save_questions(questions)

    captured = {}

    class FakeTavilyClient:
        def __init__(self, api_key, timeout):
            pass

        def search(self, query):
            return [SearchHit("行业报告", "https://example.com/r", "报告摘录。", date(2026, 1, 1))]

    class FakeDifyWorkflowClient:
        def __init__(self, base_url, api_key, timeout=60.0):
            assert api_key == "df-ev"

        def run(self, inputs, user="UT-01"):
            captured["inputs"] = inputs
            return online_research.WorkflowResult(
                "run-1",
                "succeeded",
                {
                    "evidence": [
                        {
                            "dimension": "市场规模与 CAGR",
                            "claim": "市场规模约 100 亿元（示例）",
                            "source_url": "https://example.com/r",
                            "evidence_quote": "报告称市场规模约 100 亿元。",
                            "geography": "中国",
                            "period": "2024",
                            "unit": "人民币亿元",
                            "definition_scope": "示例口径",
                            "category": "market",
                            "risk_flags": [],
                        }
                    ]
                },
            )

    monkeypatch.setattr(online_research, "TavilyClient", FakeTavilyClient)
    monkeypatch.setattr(online_research, "DifyWorkflowClient", FakeDifyWorkflowClient)
    result = run_online_research(
        repo,
        project_id,
        OnlineResearchConfig(tavily_api_key="tv-test", dify_evidence_api_key="df-ev"),
    )

    assert result.status == "succeeded"
    assert result.provider_mode == "tavily+dify"
    assert set(captured["inputs"]) == {"topic", "geography", "time_range", "questions", "sources"}
    assert isinstance(captured["inputs"]["questions"], dict)
    assert captured["inputs"]["questions"]["items"] == [question.model_dump() for question in questions]
    assert isinstance(captured["inputs"]["sources"], dict)
    assert captured["inputs"]["sources"]["items"][0]["url"] == "https://example.com/r"


def test_run_online_research_serializes_published_date_for_dify_payload(tmp_path, monkeypatch):
    """真实 SearchHit.published_date 是 date 对象，发给 Dify 前必须转成 ISO 字符串，否则 json.dumps 崩溃。"""
    import json

    repo = WorkbenchRepository(tmp_path / "date.sqlite3")
    project_id = create_online_project(repo, "四足机器人", "中国", "2024–2026", "内部讨论")
    questions = [question.model_copy(update={"approved": True}) for question in repo.list_questions(project_id)]
    repo.save_questions(questions)
    captured = {}

    class FakeTavilyClient:
        def __init__(self, api_key, timeout):
            pass

        def search(self, query):
            return [SearchHit("四足机器人报告", "https://example.com/quad", "四足机器人市场报告摘录。", date(2025, 6, 1), raw_content="四足机器人正文。")]

    class FakeDifyWorkflowClient:
        def __init__(self, base_url, api_key, timeout=60.0):
            pass

        def run(self, inputs, user="UT-01"):
            captured["inputs"] = inputs
            json.dumps(inputs)  # 必须可序列化
            return online_research.WorkflowResult("run-1", "succeeded", {"evidence": []})

    monkeypatch.setattr(online_research, "TavilyClient", FakeTavilyClient)
    monkeypatch.setattr(online_research, "DifyWorkflowClient", FakeDifyWorkflowClient)
    result = run_online_research(
        repo,
        project_id,
        OnlineResearchConfig(tavily_api_key="tv-test", dify_evidence_api_key="df-ev"),
    )
    assert result.status == "succeeded"
    payload_source = captured["inputs"]["sources"]["items"][0]
    assert payload_source["published_date"] == "2025-06-01"
    assert isinstance(payload_source["published_date"], str)


def test_generate_brief_with_dify_wraps_evidence_in_items_object(tmp_path, monkeypatch):
    from src.domain import EvidenceRecord, ReviewStatus

    record = EvidenceRecord(
        id="ev-1",
        project_id="p-1",
        question_id="q-1",
        dimension="市场规模与 CAGR",
        claim="示例主张",
        source_id="src-1",
        source_title="示例来源",
        source_url="https://example.com/s",
        source_accessible=True,
        publication_date=date(2026, 1, 1),
        evidence_quote="示例引文。",
        geography="中国",
        period="2024",
        unit="人民币亿元",
        definition_scope="示例口径",
        category="market",
        risk_flags=[],
        review_status=ReviewStatus.CONFIRMED,
    )
    captured = {}

    class FakeDifyWorkflowClient:
        def __init__(self, base_url, api_key, timeout=60.0):
            assert api_key == "df-br"

        def run(self, inputs, user="UT-01"):
            captured["inputs"] = inputs
            return online_research.WorkflowResult("run-b", "succeeded", {"markdown": "# 简报"})

    monkeypatch.setattr(online_research, "DifyWorkflowClient", FakeDifyWorkflowClient)
    repo = WorkbenchRepository(tmp_path / "brief.sqlite3")
    project_id = create_online_project(repo, "具身智能", "中国", "2024–2026", "内部讨论")
    project = online_research.Project(id=project_id, topic="具身智能", geography="中国", time_range="2024–2026", purpose="内部讨论")
    markdown = online_research.generate_brief_with_dify(OnlineResearchConfig(dify_brief_api_key="df-br"), project, [record])

    assert markdown == "# 简报"
    assert isinstance(captured["inputs"]["evidence"], dict)
    assert captured["inputs"]["evidence"]["items"][0]["id"] == "ev-1"
