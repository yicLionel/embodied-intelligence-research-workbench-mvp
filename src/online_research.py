from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx

from src.demo import DIMENSIONS
from src.domain import EvidenceRecord, Project, ResearchQuestion, SourceRecord

QUESTION_TEMPLATES = {
    "市场定义与边界": "如何定义 {topic}，与人形机器人、工业机器人等相邻概念的边界是什么？",
    "市场规模与 CAGR": "{topic} 的市场规模、增长率与预测口径是什么？",
    "产业链与关键环节": "{topic} 的上游零部件、中游平台和下游应用有哪些关键环节？",
    "竞争格局与标杆公司": "{topic} 的主要参与者、技术路线与竞争格局是什么？",
    "技术趋势与能力演进": "{topic} 的关键技术趋势、模型能力和产品演进是什么？",
    "融资活动与商业化进展": "{topic} 的融资活动、订单、试点和商业化进展是什么？",
    "风险、争议与关键假设": "{topic} 的产业化风险、争议和关键假设有哪些？",
}


@dataclass(frozen=True)
class OnlineResearchConfig:
    dify_base_url: str = "https://api.dify.ai/v1"
    tavily_api_key: str = ""
    dify_plan_api_key: str = ""
    dify_evidence_api_key: str = ""
    dify_brief_api_key: str = ""
    timeout_seconds: float = 60.0

    @classmethod
    def from_env(cls) -> OnlineResearchConfig:
        return cls(
            dify_base_url=os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1"),
            tavily_api_key=os.getenv("TAVILY_API_KEY", ""),
            dify_plan_api_key=os.getenv("DIFY_PLAN_API_KEY", ""),
            dify_evidence_api_key=os.getenv("DIFY_EVIDENCE_API_KEY", ""),
            dify_brief_api_key=os.getenv("DIFY_BRIEF_API_KEY", ""),
            timeout_seconds=float(os.getenv("ONLINE_RESEARCH_TIMEOUT", "60")),
        )

    @property
    def missing_keys(self) -> list[str]:
        required = [("TAVILY_API_KEY", self.tavily_api_key)]
        return [name for name, value in required if not value]

    @property
    def optional_missing_keys(self) -> list[str]:
        optional = [("DIFY_EVIDENCE_API_KEY", self.dify_evidence_api_key), ("DIFY_BRIEF_API_KEY", self.dify_brief_api_key)]
        return [name for name, value in optional if not value]

    @property
    def ready_for_search(self) -> bool:
        return bool(self.tavily_api_key)


@dataclass(frozen=True)
class WorkflowResult:
    run_id: str | None
    status: str
    outputs: dict[str, Any]
    error: str | None = None


@dataclass(frozen=True)
class SearchHit:
    title: str
    url: str
    content: str
    published_date: date
    source_role: str = "lead"
    raw_content: str = ""


@dataclass
class ResearchRunResult:
    project_id: str
    status: str
    source_count: int = 0
    evidence_count: int = 0
    run_id: str | None = None
    errors: list[str] = field(default_factory=list)
    provider_mode: str = "none"


def canonical_url(url: str) -> str:
    parsed = urlsplit(url.strip())
    query = [(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True) if not key.lower().startswith(("utm_", "gclid", "fbclid"))]
    path = parsed.path.rstrip("/")
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, urlencode(query), ""))


def generate_queries(topic: str, geography: str, time_range: str, dimension: str) -> list[str]:
    focus = QUESTION_TEMPLATES.get(dimension, f"{topic} {dimension}").format(topic=topic)
    return [
        f"{topic} {geography} {dimension} {time_range} 报告 数据",
        f"{focus} {geography} {time_range}",
        f"{topic} {dimension} China embodied intelligence report {time_range}",
    ]


def parse_workflow_output(outputs: dict[str, Any]) -> dict[str, Any]:
    candidate: Any = outputs
    if "outputs" in outputs and isinstance(outputs["outputs"], dict):
        candidate = outputs["outputs"]
    for key in ("result", "evidence_bundle", "brief_bundle", "text", "output"):
        if isinstance(candidate, dict) and key in candidate:
            candidate = candidate[key]
            break
    if isinstance(candidate, str):
        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else {"result": parsed}
        except json.JSONDecodeError:
            return {"text": candidate}
    return candidate if isinstance(candidate, dict) else {"result": candidate}


class DifyWorkflowClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 60.0, transport: httpx.BaseTransport | None = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.transport = transport

    def run(self, inputs: dict[str, Any], user: str = "UT-01") -> WorkflowResult:
        request_body = {"inputs": inputs, "response_mode": "blocking", "user": user}
        kwargs: dict[str, Any] = {"timeout": self.timeout}
        if self.transport is not None:
            kwargs["transport"] = self.transport
        with httpx.Client(**kwargs) as client:
            response = client.post(f"{self.base_url}/workflows/run", headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, json=request_body)
        if response.status_code in {429, 500, 502, 503, 504}:
            time.sleep(0.5)
            with httpx.Client(**kwargs) as client:
                response = client.post(f"{self.base_url}/workflows/run", headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, json=request_body)
        if response.is_error:
            return WorkflowResult(None, "failed", {}, f"Dify HTTP {response.status_code}: {response.text[:240]}")
        payload = response.json()
        data = payload.get("data", payload)
        return WorkflowResult(payload.get("workflow_run_id") or data.get("id"), data.get("status", payload.get("status", "succeeded")), parse_workflow_output(data.get("outputs", data)), data.get("error"))


class TavilyClient:
    def __init__(self, api_key: str, timeout: float = 60.0, transport: httpx.BaseTransport | None = None):
        self.api_key = api_key
        self.timeout = timeout
        self.transport = transport

    def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"timeout": self.timeout}
        if self.transport is not None:
            kwargs["transport"] = self.transport
        with httpx.Client(**kwargs) as client:
            response = client.post(f"https://api.tavily.com/{endpoint}", json={"api_key": self.api_key, **payload})
        response.raise_for_status()
        return response.json()

    def search(self, query: str, max_results: int = 5) -> list[SearchHit]:
        payload = self._post("search", {"query": query, "search_depth": "advanced", "topic": "general", "max_results": min(max_results, 5), "include_raw_content": True})
        hits: list[SearchHit] = []
        for item in payload.get("results", []):
            url = item.get("url", "")
            if not url:
                continue
            published = _parse_date(item.get("published_date")) or datetime.now(timezone.utc).date()
            hits.append(SearchHit(item.get("title", url), canonical_url(url), item.get("content", ""), published, "research" if item.get("score", 0) >= 0.7 else "lead", item.get("raw_content", "")))
        return hits


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _stable_id(prefix: str, value: str) -> str:
    return f"{prefix}-{hashlib.sha1(value.encode('utf-8')).hexdigest()[:12]}"


def create_online_project(repo: Any, topic: str, geography: str, time_range: str, purpose: str, focus_questions: str = "") -> str:
    project_id = _stable_id("online", f"{topic}|{geography}|{time_range}|{purpose}")
    repo.save_project(Project(id=project_id, topic=topic, geography=geography, time_range=time_range, purpose=purpose, focus_questions=focus_questions))
    questions = [ResearchQuestion(id=f"{project_id}-q-{index + 1}", project_id=project_id, dimension=dimension, text=QUESTION_TEMPLATES[dimension].format(topic=topic), priority=2) for index, dimension in enumerate(DIMENSIONS)]
    repo.save_questions(questions)
    return project_id


def _category(dimension: str) -> str:
    if dimension == "市场规模与 CAGR":
        return "market"
    if dimension == "技术趋势与能力演进":
        return "technology"
    if dimension == "融资活动与商业化进展":
        return "commercialization"
    if dimension == "产业链与关键环节":
        return "supply_chain"
    return "industry"


def _fallback_evidence(project: Project, questions: list[ResearchQuestion], hits_by_dimension: dict[str, list[SearchHit]]) -> list[EvidenceRecord]:
    records: list[EvidenceRecord] = []
    for question in questions:
        if question.deleted:
            continue
        dimension = question.dimension
        matching = (hits_by_dimension.get(dimension) or [None])[0]
        if not matching:
            continue
        quote = (matching.raw_content or matching.content).strip().replace("\n", " ")[:900]
        claim = re.split(r"(?<=[。.!?])\s+", quote)[0][:240] or matching.title
        records.append(EvidenceRecord(id=_stable_id("ev", f"{project.id}|{question.id}|{matching.url}"), project_id=project.id, question_id=question.id, dimension=dimension, claim=claim, source_id=_stable_id("src", matching.url), source_title=matching.title, source_url=matching.url, source_reference="Tavily 检索结果摘录；待人工回查原文", source_accessible=True, publication_date=matching.published_date, evidence_quote=quote, geography=project.geography, period=project.time_range, definition_scope=project.topic, category=_category(dimension), risk_flags=["missing_evidence"] if not quote else []))
    return records


def run_online_research(repo: Any, project_id: str, config: OnlineResearchConfig | None = None, user: str = "UT-01") -> ResearchRunResult:
    config = config or OnlineResearchConfig.from_env()
    project = repo.get_project(project_id)
    if project is None:
        return ResearchRunResult(project_id, "failed", errors=["project_not_found"])
    if not config.ready_for_search:
        return ResearchRunResult(project_id, "blocked", errors=[f"缺少配置：{', '.join(config.missing_keys)}"])
    questions = [question for question in repo.list_questions(project_id) if not question.deleted]
    tavily = TavilyClient(config.tavily_api_key, config.timeout_seconds)
    hits: dict[str, SearchHit] = {}
    hits_by_dimension: dict[str, list[SearchHit]] = {}
    errors: list[str] = []
    for question in questions:
        for query in generate_queries(project.topic, project.geography, project.time_range, question.dimension):
            try:
                for hit in tavily.search(query):
                    hits.setdefault(hit.url, hit)
                    dimension_hits = hits_by_dimension.setdefault(question.dimension, [])
                    if all(existing.url != hit.url for existing in dimension_hits):
                        dimension_hits.append(hit)
            except (httpx.HTTPError, ValueError) as exc:
                errors.append(f"{question.dimension}: {str(exc)[:160]}")
    hit_list = list(hits.values())
    sources = [SourceRecord(id=_stable_id("src", hit.url), project_id=project_id, title=hit.title, organization=urlsplit(hit.url).netloc, source_role=hit.source_role, publication_date=hit.published_date, url=hit.url, reference="Tavily public web search; publication date may be unavailable") for hit in hit_list]
    if sources:
        repo.save_sources(sources)
    evidence = _fallback_evidence(project, questions, hits_by_dimension)
    if config.dify_evidence_api_key and hit_list:
        client = DifyWorkflowClient(config.dify_base_url, config.dify_evidence_api_key, config.timeout_seconds)
        workflow = client.run({"topic": project.topic, "geography": project.geography, "time_range": project.time_range, "questions": [question.model_dump() for question in questions], "sources": [hit.__dict__ for hit in hit_list[:30]]}, user=user)
        if workflow.status == "succeeded":
            parsed = workflow.outputs.get("evidence") if isinstance(workflow.outputs, dict) else None
            if isinstance(parsed, list):
                evidence = _evidence_from_dify(project, questions, parsed, sources) or evidence
            return _save_result(repo, project_id, sources, evidence, errors, workflow.run_id, "tavily+dify")
        errors.append(workflow.error or "Dify evidence workflow failed")
    return _save_result(repo, project_id, sources, evidence, errors, None, "tavily")


def _evidence_from_dify(project: Project, questions: list[ResearchQuestion], items: list[dict[str, Any]], sources: list[SourceRecord]) -> list[EvidenceRecord]:
    by_url = {source.url: source for source in sources}
    by_dimension = {question.dimension: question for question in questions}
    records: list[EvidenceRecord] = []
    for index, item in enumerate(items):
        dimension = item.get("dimension") or item.get("category") or questions[index % len(questions)].dimension
        question = by_dimension.get(dimension, questions[index % len(questions)])
        url = canonical_url(item.get("source_url") or item.get("url") or "")
        source = by_url.get(url) or sources[index % len(sources)]
        quote = str(item.get("evidence_quote") or item.get("quote") or "").strip()
        records.append(EvidenceRecord(id=_stable_id("ev", f"{project.id}|{question.id}|{index}|{url}"), project_id=project.id, question_id=question.id, dimension=question.dimension, claim=str(item.get("claim") or "证据不足"), source_id=source.id, source_title=source.title, source_url=source.url, source_reference=source.reference, source_accessible=source.accessible, publication_date=source.publication_date, evidence_quote=quote, geography=item.get("geography") or project.geography, period=item.get("period") or project.time_range, unit=item.get("unit"), definition_scope=item.get("definition_scope") or project.topic, category=item.get("category") or _category(question.dimension), risk_flags=list(item.get("risk_flags") or (["missing_evidence"] if not quote else []))) )
    return records


def _save_result(repo: Any, project_id: str, sources: list[SourceRecord], evidence: list[EvidenceRecord], errors: list[str], run_id: str | None, mode: str) -> ResearchRunResult:
    if evidence:
        repo.save_evidence(evidence)
    return ResearchRunResult(project_id, "succeeded" if sources else "partial", len(sources), len(evidence), run_id, errors, mode)


def generate_brief_with_dify(config: OnlineResearchConfig, project: Project, evidence: list[EvidenceRecord], user: str = "UT-01") -> str | None:
    if not config.dify_brief_api_key or not evidence:
        return None
    client = DifyWorkflowClient(config.dify_base_url, config.dify_brief_api_key, config.timeout_seconds)
    result = client.run({"topic": project.topic, "geography": project.geography, "time_range": project.time_range, "evidence": [item.model_dump(mode="json") for item in evidence if item.can_confirm and item.review_status.value == "confirmed"]}, user=user)
    if result.status != "succeeded":
        return None
    return str(result.outputs.get("markdown") or result.outputs.get("brief_markdown") or result.outputs.get("text") or "") or None
