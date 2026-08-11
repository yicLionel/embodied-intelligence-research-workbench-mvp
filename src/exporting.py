from __future__ import annotations

import csv
import io

from src.briefs import Brief
from src.domain import EvidenceRecord


def evidence_csv(evidence: list[EvidenceRecord]) -> bytes:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["id", "claim", "source_title", "review_status", "risk_flags", "evidence_quote"])
    writer.writeheader()
    for item in evidence:
        writer.writerow({"id": item.id, "claim": item.claim, "source_title": item.source_title, "review_status": item.review_status.value, "risk_flags": ";".join(item.risk_flags), "evidence_quote": item.evidence_quote})
    return output.getvalue().encode("utf-8-sig")


def formal_markdown(brief: Brief) -> str:
    if brief.mode != "formal":
        raise ValueError("只有正式简报可以导出")
    return "# 正式研究简报\n\n" + "\n".join(f"- {item.text}" for item in brief.sentences)
