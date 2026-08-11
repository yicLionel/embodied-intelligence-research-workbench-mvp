from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from src.domain import (
    EvidenceRecord,
    Project,
    ResearchQuestion,
    ReviewStatus,
    SourceRecord,
)


class WorkbenchRepository:
    def __init__(self, path: str | Path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _initialize(self) -> None:
        with self.connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, topic TEXT, geography TEXT, time_range TEXT, purpose TEXT, focus_questions TEXT);
            CREATE TABLE IF NOT EXISTS questions (id TEXT PRIMARY KEY, project_id TEXT REFERENCES projects(id), dimension TEXT, text TEXT, priority INTEGER, approved INTEGER, deleted INTEGER);
            CREATE TABLE IF NOT EXISTS sources (id TEXT PRIMARY KEY, project_id TEXT REFERENCES projects(id), title TEXT, organization TEXT, source_role TEXT, publication_date TEXT, url TEXT, reference TEXT, accessible INTEGER, extraction_status TEXT, excluded INTEGER);
            CREATE TABLE IF NOT EXISTS evidence (id TEXT PRIMARY KEY, project_id TEXT REFERENCES projects(id), question_id TEXT, dimension TEXT, claim TEXT, source_id TEXT REFERENCES sources(id), source_title TEXT, source_url TEXT, source_reference TEXT, source_accessible INTEGER, publication_date TEXT, evidence_quote TEXT, geography TEXT, period TEXT, unit TEXT, definition_scope TEXT, category TEXT, risk_flags TEXT, review_status TEXT);
            CREATE TABLE IF NOT EXISTS checkpoints (project_id TEXT PRIMARY KEY REFERENCES projects(id), status TEXT, completed_units TEXT, error TEXT, updated_at TEXT);
            """)

    @contextmanager
    def transaction(self):
        conn = self.connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def save_project(self, project: Project) -> None:
        with self.transaction() as c:
            c.execute("INSERT OR REPLACE INTO projects VALUES (?, ?, ?, ?, ?, ?)", tuple(project.model_dump().values()))

    def get_project(self, project_id: str) -> Project | None:
        with self.connection() as c:
            row = c.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        return Project.model_validate(dict(row)) if row else None

    def save_questions(self, questions: list[ResearchQuestion]) -> None:
        with self.transaction() as c:
            for q in questions:
                c.execute("INSERT OR REPLACE INTO questions VALUES (?, ?, ?, ?, ?, ?, ?)", (*q.model_dump(exclude={"approved", "deleted"}).values(), int(q.approved), int(q.deleted)))

    def list_questions(self, project_id: str) -> list[ResearchQuestion]:
        with self.connection() as c:
            rows = c.execute("SELECT * FROM questions WHERE project_id=? ORDER BY dimension,id", (project_id,)).fetchall()
        return [ResearchQuestion.model_validate({**dict(r), "approved": bool(r["approved"]), "deleted": bool(r["deleted"])}) for r in rows]

    def save_sources(self, sources: list[SourceRecord]) -> None:
        with self.transaction() as c:
            for s in sources:
                d = s.model_dump(); d["publication_date"] = d["publication_date"].isoformat(); d["accessible"] = int(d["accessible"]); d["excluded"] = int(d["excluded"])
                c.execute("INSERT OR REPLACE INTO sources VALUES (:id,:project_id,:title,:organization,:source_role,:publication_date,:url,:reference,:accessible,:extraction_status,:excluded)", d)

    def list_sources(self, project_id: str) -> list[SourceRecord]:
        with self.connection() as c: rows = c.execute("SELECT * FROM sources WHERE project_id=? ORDER BY publication_date DESC", (project_id,)).fetchall()
        return [SourceRecord.model_validate({**dict(r), "accessible": bool(r["accessible"]), "excluded": bool(r["excluded"])}) for r in rows]

    def save_evidence(self, records: list[EvidenceRecord]) -> None:
        with self.transaction() as c:
            for e in records:
                d=e.model_dump(); d["publication_date"]=d["publication_date"].isoformat(); d["source_accessible"]=int(d["source_accessible"]); d["risk_flags"]=json.dumps(d["risk_flags"]); d["review_status"]=d["review_status"].value
                c.execute("INSERT OR REPLACE INTO evidence VALUES (:id,:project_id,:question_id,:dimension,:claim,:source_id,:source_title,:source_url,:source_reference,:source_accessible,:publication_date,:evidence_quote,:geography,:period,:unit,:definition_scope,:category,:risk_flags,:review_status)",d)

    def list_evidence(self, project_id: str) -> list[EvidenceRecord]:
        with self.connection() as c: rows=c.execute("SELECT * FROM evidence WHERE project_id=?",(project_id,)).fetchall()
        return [EvidenceRecord.model_validate({**dict(r), "source_accessible":bool(r["source_accessible"]),"risk_flags":json.loads(r["risk_flags"])}) for r in rows]

    def set_review_status(self, evidence_id: str, status: ReviewStatus) -> None:
        with self.transaction() as c:
            row=c.execute("SELECT * FROM evidence WHERE id=?",(evidence_id,)).fetchone()
            item=EvidenceRecord.model_validate({**dict(row),"source_accessible":bool(row["source_accessible"]),"risk_flags":json.loads(row["risk_flags"])})
            c.execute("UPDATE evidence SET review_status=? WHERE id=?",(item.with_status(status).review_status.value,evidence_id))

    def exclude_source(self, source_id: str) -> None:
        with self.transaction() as c:
            c.execute("UPDATE sources SET excluded=1 WHERE id=?",(source_id,))
            c.execute("UPDATE evidence SET review_status='discarded' WHERE source_id=?",(source_id,))
