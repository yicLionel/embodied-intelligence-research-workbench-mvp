#!/usr/bin/env python3
"""Dify 集成验证脚本：用真实 key 调用云端两个 workflow，校验输出契约。

用法（先按 dify/setup-guide.md 完成搭建并配置 key）：

    python3 dify/verify_dify.py                 # 验证所有已配置的 workflow
    python3 dify/verify_dify.py --evidence-only # 只验证证据提取
    python3 dify/verify_dify.py --brief-only    # 只验证正式简报
    python3 dify/verify_dify.py --json          # 机器可读输出

配置读取顺序与应用一致：先环境变量，再回退到 .streamlit/secrets.toml。
需要 DIFY_EVIDENCE_API_KEY / DIFY_BRIEF_API_KEY（分别对应两个 workflow 应用的 API key）。

退出码：0 = 全部通过；1 = 有失败；2 = 没有任何 Dify key 可验证。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

import tomllib

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.domain import EvidenceRecord, ReviewStatus
from src.online_research import (
    DifyWorkflowClient,
    OnlineResearchConfig,
)

SAMPLE_QUESTIONS = [
    {
        "id": "vq-1",
        "dimension": "市场规模与 CAGR",
        "text": "中国人形机器人的市场规模、增长率与预测口径是什么？",
        "priority": 2,
    },
    {
        "id": "vq-2",
        "dimension": "竞争格局与标杆公司",
        "text": "中国的主要参与者、技术路线与竞争格局是什么？",
        "priority": 2,
    },
]

SAMPLE_SOURCES = [
    {
        "title": "中国信通院：人形机器人产业研究报告（示例）",
        "url": "https://example.com/caict/2024/1201",
        "content": "2024 年中国人形机器人市场规模约为 27.6 亿元，预计 2030 年将达到 870 亿元。",
        "published_date": "2024-12-01",
        "source_role": "research",
        "raw_content": "（合成示例正文）中国信通院发布报告显示，2024 年中国人形机器人市场规模约 27.6 亿元，预计 2030 年达到 870 亿元，年均复合增长率为 63.5%。",
    },
    {
        "title": "某券商机器人行业深度报告（示例）",
        "url": "https://example.com/broker/2025/0302",
        "content": "国内头部厂商在运动控制与灵巧手环节积累明显，商业化以工厂分拣与巡检场景先行。",
        "published_date": "2025-03-02",
        "source_role": "lead",
        "raw_content": "（合成示例正文）产业链上游包括行星滚柱丝杠、无框力矩电机、六维力传感器等核心零部件；中游整机厂商……",
    },
    {
        "title": "行业媒体：具身智能融资盘点（示例）",
        "url": "https://example.com/media/2025/0615",
        "content": "2025 年上半年国内具身智能领域公开融资事件超过 40 起，单笔最高超过 10 亿元。",
        "published_date": "2025-06-15",
        "source_role": "lead",
        "raw_content": "（合成示例正文）2025 年上半年国内具身智能领域公开融资事件超 40 起，单笔最高超 10 亿元。",
    },
]

EVIDENCE_CONTRACT = {
    "claim": "事实主张",
    "dimension": "所属维度",
    "source_url": "来源 URL（或 url）",
    "evidence_quote": "直接引文（或 quote）",
    "geography": "地域",
    "period": "时期",
    "definition_scope": "定义口径",
    "category": "market/technology/commercialization/supply_chain/industry",
    "risk_flags": "风险标签数组",
}


def _error_hint(error: str | None) -> str:
    if not error:
        return ""
    if "VariableEntity" in error and "type" in error:
        return (
            "开始节点的 JSON 变量类型写成了 json，Dify 运行时只认 json_object。"
            "请在 Dify 里打开开始节点，把 questions/sources/evidence 变量类型改为「JSON 对象」后重新发布；"
            "或重新导入 dify/ 下修正后的 DSL 文件。"
        )
    if "401" in error:
        return "API key 错误或应用未发布：检查 app- 前缀与应用右上角的发布状态。"
    if "404" in error:
        return "应用不存在或 DIFY_BASE_URL 写错（云上应为 https://api.dify.ai/v1）。"
    if "model" in error.lower() and ("not found" in error.lower() or "not configured" in error.lower()):
        return "LLM 节点指向的模型在你账号未配置：进应用重选模型后重新发布。"
    return ""


def load_config() -> OnlineResearchConfig:
    config = OnlineResearchConfig.from_env()

    def pick(name: str) -> str:
        current = getattr(config, name.lower())
        if current:
            return current
        return ""

    # 回退读取 Streamlit secrets（与应用 current_online_config 的行为一致）
    secrets_path = PROJECT_ROOT / ".streamlit" / "secrets.toml"
    if secrets_path.exists():
        try:
            with open(secrets_path, "rb") as handle:
                secrets = tomllib.load(handle)
        except tomllib.TOMLDecodeError as exc:
            print(f"[warn] 无法解析 {secrets_path}: {exc}", file=sys.stderr)
            secrets = {}
        for name in ("DIFY_BASE_URL", "DIFY_EVIDENCE_API_KEY", "DIFY_BRIEF_API_KEY"):
            if not pick(name) and secrets.get(name):
                config = OnlineResearchConfig(
                    dify_base_url=config.dify_base_url if name != "DIFY_BASE_URL" else secrets[name],
                    tavily_api_key=config.tavily_api_key,
                    dify_plan_api_key=config.dify_plan_api_key,
                    dify_evidence_api_key=secrets.get("DIFY_EVIDENCE_API_KEY") or config.dify_evidence_api_key,
                    dify_brief_api_key=secrets.get("DIFY_BRIEF_API_KEY") or config.dify_brief_api_key,
                    timeout_seconds=config.timeout_seconds,
                )
                break
    return config


def _run_workflow_safely(client: DifyWorkflowClient, inputs: dict[str, Any], user: str) -> dict[str, Any]:
    """调用 workflow，把网络/超时异常转成明确的失败结果而不是让脚本崩溃。"""
    import httpx

    try:
        result = client.run(inputs, user=user)
    except httpx.HTTPError as exc:
        return {
            "ok": False,
            "status": "failed",
            "error": f"请求失败（可能是超时，当前超时 {client.timeout}s）：{type(exc).__name__}: {exc}",
            "outputs": {},
        }
    return {
        "ok": result.status == "succeeded",
        "status": result.status,
        "error": result.error,
        "outputs": result.outputs,
        "run_id": result.run_id,
    }


def check_evidence(config: OnlineResearchConfig) -> dict[str, Any]:
    client = DifyWorkflowClient(config.dify_base_url, config.dify_evidence_api_key, config.timeout_seconds)
    # Dify json_object 输入变量只接受对象：数组统一包成 {"items": [...]}，由 workflow 内代码节点解包。
    outcome = _run_workflow_safely(
        client,
        {
            "topic": "人形机器人行业（验证样例）",
            "geography": "中国",
            "time_range": "2024-2026",
            "questions": {"items": SAMPLE_QUESTIONS},
            "sources": {"items": SAMPLE_SOURCES},
        },
        "verify-ut-01",
    )
    if not outcome["ok"]:
        return outcome
    result = outcome
    evidence = result["outputs"].get("evidence")
    if not isinstance(evidence, list):
        return {"ok": False, "status": result["status"], "error": "输出缺少 evidence 数组", "outputs": result["outputs"]}
    issues: list[str] = []
    if not evidence:
        issues.append(
            "证据条数为 0。若 LLM 使用了 DeepSeek 等推理模型，思考块可能污染输出导致 JSON 解析失败："
            "请确认「解析 JSON」代码节点已剥离 <think> 块（重新导入修正后的 DSL），或把 LLM 换成非推理模型（如 deepseek-chat / gpt-4o-mini）。"
        )
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            issues.append(f"evidence[{index}] 不是对象")
            continue
        for key, alias in (("claim", None), ("dimension", None), ("source_url", "url"), ("evidence_quote", "quote")):
            if not item.get(key) and not (alias and item.get(alias)):
                issues.append(f"evidence[{index}] 缺少 {key}")
        for key in ("geography", "period", "definition_scope", "category"):
            if key not in item:
                issues.append(f"evidence[{index}] 缺少可选字段 {key}")
        if "risk_flags" in item and not isinstance(item["risk_flags"], list):
            issues.append(f"evidence[{index}] risk_flags 不是数组")
    return {
        "ok": not issues,
        "status": result["status"],
        "evidence_count": len(evidence),
        "run_id": result["run_id"],
        "issues": issues,
        "evidence": evidence,
    }


def check_brief(config: OnlineResearchConfig) -> dict[str, Any]:
    sample_evidence = [
        EvidenceRecord(
            id="vev-1",
            project_id="verify-project",
            question_id="vq-1",
            dimension="市场规模与 CAGR",
            claim="2024 年中国人形机器人市场规模约 27.6 亿元（示例）",
            source_id="src-1",
            source_title="中国信通院：人形机器人产业研究报告（示例）",
            source_url="https://example.com/caict/2024/1201",
            source_accessible=True,
            publication_date=date(2024, 12, 1),
            evidence_quote="2024 年中国人形机器人市场规模约为 27.6 亿元。",
            geography="中国",
            period="2024",
            unit="人民币亿元",
            definition_scope="人形机器人整机",
            category="market",
            risk_flags=[],
            review_status=ReviewStatus.CONFIRMED,
        ).model_dump(mode="json"),
        EvidenceRecord(
            id="vev-2",
            project_id="verify-project",
            question_id="vq-2",
            dimension="竞争格局与标杆公司",
            claim="国内头部厂商在运动控制与灵巧手环节积累明显（示例）",
            source_id="src-2",
            source_title="某券商机器人行业深度报告（示例）",
            source_url="https://example.com/broker/2025/0302",
            source_accessible=True,
            publication_date=date(2025, 3, 2),
            evidence_quote="国内头部厂商在运动控制与灵巧手环节积累明显。",
            geography="中国",
            period="2025",
            unit=None,
            definition_scope="具身智能产业链",
            category="industry",
            risk_flags=[],
            review_status=ReviewStatus.CONFIRMED,
        ).model_dump(mode="json"),
    ]
    client = DifyWorkflowClient(config.dify_base_url, config.dify_brief_api_key, config.timeout_seconds)
    outcome = _run_workflow_safely(
        client,
        {
            "topic": "人形机器人行业（验证样例）",
            "geography": "中国",
            "time_range": "2024-2026",
            "evidence": {"items": sample_evidence},
        },
        "verify-ut-01",
    )
    if not outcome["ok"]:
        return outcome
    result = outcome
    markdown = (
        result["outputs"].get("markdown")
        or result["outputs"].get("brief_markdown")
        or result["outputs"].get("text")
        or ""
    )
    return {
        "ok": bool(str(markdown).strip()),
        "status": result["status"],
        "markdown_length": len(str(markdown)),
        "run_id": result["run_id"],
        "error": None if str(markdown).strip() else "输出缺少 markdown/brief_markdown/text 文本",
        "markdown_preview": str(markdown)[:300],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="验证 Dify evidence/brief workflow 输出契约")
    parser.add_argument("--json", action="store_true", help="机器可读 JSON 输出")
    parser.add_argument("--evidence-only", action="store_true")
    parser.add_argument("--brief-only", action="store_true")
    parser.add_argument("--timeout", type=float, help="请求超时秒数（覆盖 ONLINE_RESEARCH_TIMEOUT）")
    args = parser.parse_args()

    config = load_config()
    if args.timeout:
        config = OnlineResearchConfig(
            dify_base_url=config.dify_base_url,
            tavily_api_key=config.tavily_api_key,
            dify_plan_api_key=config.dify_plan_api_key,
            dify_evidence_api_key=config.dify_evidence_api_key,
            dify_brief_api_key=config.dify_brief_api_key,
            timeout_seconds=args.timeout,
        )
    results: dict[str, Any] = {"config": {"base_url": config.dify_base_url}}
    results["config"]["evidence_key"] = bool(config.dify_evidence_api_key)
    results["config"]["brief_key"] = bool(config.dify_brief_api_key)

    do_evidence = (not args.brief_only) and bool(config.dify_evidence_api_key)
    do_brief = (not args.evidence_only) and bool(config.dify_brief_api_key)

    if not do_evidence and not do_brief:
        msg = (
            "未找到任何 Dify API key（DIFY_EVIDENCE_API_KEY / DIFY_BRIEF_API_KEY）。\n"
            "请先按 dify/setup-guide.md 完成云端搭建，再把 key 写入环境变量或 .streamlit/secrets.toml。"
        )
        if args.json:
            print(json.dumps({"ok": False, "skipped": True, "message": msg}, ensure_ascii=False, indent=2))
        else:
            print(msg)
        return 2

    if do_evidence:
        results["evidence"] = check_evidence(config)
    if do_brief:
        results["brief"] = check_brief(config)

    all_ok = all(results.get(k, {}).get("ok") for k in ("evidence", "brief") if k in results)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
    else:
        for key in ("evidence", "brief"):
            if key not in results:
                continue
            r = results[key]
            status = "✅ 通过" if r.get("ok") else "❌ 失败"
            print(f"[{key}] {status}  status={r.get('status')}")
            if key == "evidence":
                print(f"    证据条数: {r.get('evidence_count')}  run_id: {r.get('run_id')}")
                for issue in r.get("issues", []):
                    print(f"    - {issue}")
            else:
                print(f"    markdown 长度: {r.get('markdown_length')}  run_id: {r.get('run_id')}")
                if r.get("markdown_preview"):
                    print(f"    预览: {r['markdown_preview']!r}...")
            if r.get("error"):
                print(f"    错误: {r['error']}")
                hint = _error_hint(r["error"])
                if hint:
                    print(f"    💡 {hint}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
