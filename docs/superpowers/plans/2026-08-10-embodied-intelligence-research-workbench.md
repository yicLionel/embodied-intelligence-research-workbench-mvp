# Embodied Intelligence Research Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 2–3 week B-lite MVP that lets boutique-FA junior analysts define an embodied-intelligence research task, approve a question framework, collect traceable evidence, review quality risks, and generate an evidence-backed Chinese research brief.

**Architecture:** Use Dify Cloud for three low-code workflows—research planning, evidence collection, and brief generation—connected to a thin Streamlit multipage workbench. Streamlit owns human review, deterministic quality rules, SQLite persistence, exports, and evaluation; Dify owns model/tool orchestration. Public web evidence comes from the Dify Tavily plugin, while local PDF/TXT/Markdown supplements are parsed and chunked in the Streamlit app before selected excerpts are sent to Dify.

**Tech Stack:** Python 3.12; Streamlit 1.51.0; Dify Cloud Workflows; Dify Tavily plugin 0.1.11; OpenAI `gpt-5.4-mini` with low reasoning effort; SQLite; Pydantic 2; HTTPX; pandas; pypdf; pytest; Streamlit AppTest; Ruff; GitHub Actions; Streamlit Community Cloud.

## Global Constraints

- The first user is a boutique-FA intern or junior analyst; do not add investor, founder, or administrator personas.
- The only launch domain is embodied intelligence: China commercialization, financing, and supply chain, with global technology and benchmark-company comparison.
- Every project accepts at most 5 supplemental items; allowed files are PDF, TXT, and Markdown; each file is at most 20 MiB; URLs count toward the 5-item limit.
- The app has five stages: research task, framework, sources, evidence matrix, and brief.
- The app has no account system, payments, team permissions, sourcing, company recommendation, monitoring, PPT generation, or autonomous investment decisions.
- A claim without a directly supporting quote or accessible source cannot be confirmed and cannot enter either a candidate preview or a formal/exportable brief.
- A candidate preview is clearly labeled pending/unconfirmed and non-exportable; it may use only accessible, directly quoted candidate evidence and must show citations and risk labels. A formal/exportable brief may use only user-confirmed evidence.
- Market figures require geography, period, unit, and definition scope; different definitions stay separate.
- Company/commercialization/financing sources older than 12 months and market/supply-chain reports older than 24 months receive `possibly_stale`; history, standards, and technical-principle sources are exempt from automatic staleness.
- Dify and provider keys stay in `.streamlit/secrets.toml` locally and Streamlit Community Cloud Secrets in deployment; never commit them.
- The MVP acceptance targets are: evidence support ≥85%, accessible citations ≥90%, key-field completeness ≥85%, severe factual errors ≤1/30, task-time improvement ≥30%, and at least 3 users who judge the product work-usable and say they would use it again.
- All automated tests run without live Dify, Tavily, or OpenAI calls; live-provider tests are a separately invoked smoke test.
- Keep commits task-scoped and use Conventional Commit prefixes.

## Planned File Structure

```text
.
├── streamlit_app.py                  # App entrypoint and five-stage navigation
├── app/
│   ├── state.py                      # Session/project selection helpers
│   └── pages/
│       ├── task_setup.py             # Research-task input and project creation
│       ├── framework.py              # Question-tree review and confirmation
│       ├── sources.py                # Source list and ingestion warnings
│       ├── evidence.py               # Evidence matrix, detail, and review actions
│       └── brief.py                  # Brief generation, validation, and export
├── src/
│   ├── config.py                     # Constants and secret loading
│   ├── domain.py                     # Pydantic domain contracts and enums
│   ├── storage.py                    # SQLite schema and repository
│   ├── ingestion.py                  # File/URL validation, text extraction, chunking
│   ├── dify_client.py                # Typed Dify Workflow API client
│   ├── quality.py                    # Deterministic risk and completeness rules
│   ├── brief_validation.py           # Sentence-to-evidence mapping guardrail
│   ├── exporting.py                  # CSV and Markdown serializers
│   └── telemetry.py                  # Local event and timing records
├── prompts/
│   ├── research_plan.md              # Question-tree prompt
│   ├── evidence_extraction.md        # Evidence extraction prompt and schema rules
│   └── brief_generation.md           # Candidate-preview and confirmed-evidence formal brief prompt
├── schemas/
│   ├── research_framework.schema.json
│   ├── evidence_bundle.schema.json
│   └── brief_bundle.schema.json
├── workflows/
│   ├── research_plan.yml             # Exported Dify DSL
│   ├── evidence_collection.yml       # Exported Dify DSL with Tavily
│   └── brief_generation.yml          # Exported Dify DSL
├── evals/
│   ├── questions.csv                 # 30-question offline evaluation set
│   ├── gold/                         # Human reference answers and accepted sources
│   └── runs/.gitkeep                 # Local run outputs; JSON results ignored
├── scripts/
│   ├── validate_workflows.py         # Dify input/output contract validator
│   ├── run_eval.py                   # Offline evaluation runner
│   └── smoke_live.py                 # Explicit live-provider smoke test
├── tests/
│   ├── fixtures/                     # Provider payloads and sample documents
│   ├── test_domain.py
│   ├── test_storage.py
│   ├── test_ingestion.py
│   ├── test_dify_client.py
│   ├── test_schemas.py
│   ├── test_quality.py
│   ├── test_brief_validation.py
│   ├── test_exporting.py
│   ├── test_telemetry.py
│   ├── test_eval.py
│   └── test_app.py
├── docs/
│   ├── discovery-interviews.md       # Pre-build workflow and problem evidence
│   ├── runbook.md                    # Setup, Dify configuration, and deployment
│   ├── user-test-script.md           # 3–5 user test protocol
│   └── portfolio-case-study.md       # Evidence-first interview narrative
├── .github/workflows/ci.yml
├── .streamlit/config.toml
├── .env.example
├── requirements.txt
└── requirements-dev.txt
```

---

### Task 0: Pre-Build Problem Validation and Baseline

**Files:**
- Create: `docs/discovery-interviews.md`

**Interfaces:**
- Consumes: 2–3 interviews with boutique-FA interns or junior analysts who completed an industry-research task in the previous 90 days.
- Produces: anonymized current-state workflow, baseline time ranges, ranked pain points, design implications, and a documented go/no-go decision for the confirmed MVP scope.

- [ ] **Step 1: Write the interview guide before recruiting**

Use the same questions for every participant: recent research task and deadline; exact steps and tools; time by step; repeated or copied work; source/citation failure cases; review and correction process; confidentiality constraints; reaction to framework → evidence → brief; and the one condition that would stop them using it. The checkpoint question must distinguish a clearly labeled non-exportable preview, built only from accessible directly quoted candidate evidence with visible citations/pending status, from a formal/exportable brief built only from user-confirmed evidence after high-risk/key-data review. Do not pitch features until the current workflow is reconstructed.

- [ ] **Step 2: Conduct and anonymize 2–3 interviews**

Use session codes `DV-01` onward. Do not record names, employer names, client names, deal details, emails, or confidential documents. Record time estimates as participant-reported ranges and label them as such.

- [ ] **Step 3: Synthesize the baseline**

`docs/discovery-interviews.md` must contain:

1. Participant table with session code, role level, recency of research work, and no identifying details.
2. Current-state workflow with median reported time range for scoping, search, extraction, reconciliation, citation cleanup, and writing. If eligible participants provide only total task duration, record that participant-reported limitation explicitly; do not invent a step allocation or median, and measure step durations in Task 10.
3. Pain-point ranking using frequency × severity, with raw participant count beside each item.
4. Evidence supporting or contradicting the selected user, embodied-intelligence pilot, and evidence-first workflow.
5. Product changes made from interviews; if none, state why the confirmed scope remains appropriate.
6. Baseline-task definition reused in Task 10 user tests so the ≥30% time-improvement comparison is valid.

- [ ] **Step 4: Apply the go/no-go gate**

Proceed unchanged only if at least 2 participants report material repetitive search/extraction/citation work and accept the standardized checkpoint: a clearly labeled non-exportable preview using only accessible directly quoted candidate evidence, followed by high-risk/key-data review before a formal/exportable brief using only user-confirmed evidence. Otherwise revise the target workflow in both the design spec and this plan before writing product code.

- [ ] **Step 5: Review and commit**

Run: `rg -n "@|客户|项目代号|公司全名" docs/discovery-interviews.md`

Expected: no personally identifying or confidential content; any benign match is manually reviewed.

```bash
git add docs/discovery-interviews.md
git commit -m "docs: validate FA research workflow"
```

---

### Task 1: Application Foundation and Domain Contracts

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `.env.example`
- Create: `.streamlit/config.toml`
- Create: `streamlit_app.py`
- Create: `app/state.py`
- Create: `app/pages/task_setup.py`
- Create: `app/pages/framework.py`
- Create: `app/pages/sources.py`
- Create: `app/pages/evidence.py`
- Create: `app/pages/brief.py`
- Create: `src/config.py`
- Create: `src/domain.py`
- Create: `tests/test_domain.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: None.
- Produces: `ProjectStage`, `ReviewStatus`, `SourceType`, `RiskFlag`, `AccessStatus`, `ExtractionStatus`, `EvidenceCategory`, `WorkflowStatus`, `BriefMode`, `SupplementalItem`, `ResearchProject`, `ResearchQuestion`, `SourceRecord`, `EvidenceRecord`, `WorkflowCheckpoint`, `ClaimEvidenceMap`, and `BriefBundle`; `BriefBundle.mode` is `preview` or `formal`; `get_project_id()` / `set_project_id()` session helpers; a runnable five-page Streamlit shell.

- [ ] **Step 1: Add dependency and secret templates**

Write `requirements.txt` with:

```text
streamlit==1.51.0
pydantic>=2.11,<3
httpx>=0.28,<1
pandas>=2.2,<3
pypdf>=5,<6
PyYAML>=6,<7
```

Write `requirements-dev.txt` with:

```text
-r requirements.txt
pytest>=8,<9
pytest-cov>=6,<7
ruff>=0.12,<1
jsonschema>=4,<5
```

Write `.env.example` with names but no values:

```dotenv
DIFY_BASE_URL=https://api.dify.ai/v1
DIFY_PLAN_API_KEY=
DIFY_EVIDENCE_API_KEY=
DIFY_BRIEF_API_KEY=
APP_DB_PATH=data/workbench.sqlite3
```

Add `.streamlit/secrets.toml`, `data/*.sqlite3`, and `evals/runs/*.json` to `.gitignore`.

- [ ] **Step 2: Write failing domain tests**

```python
# tests/test_domain.py
from datetime import date
from src.domain import EvidenceRecord, ReviewStatus


def test_confirmed_evidence_requires_quote_and_accessible_url():
    evidence = EvidenceRecord.model_validate({
        "id": "ev-1",
        "project_id": "pr-1",
        "research_question_id": "rq-1",
        "research_question": "中国具身智能处于哪个商业化阶段？",
        "source_id": "src-1",
        "category": "commercialization",
        "claim": "中国具身智能市场进入商业化早期。",
        "geography": "中国",
        "period": "2026",
        "definition_scope": "具身智能机器人",
        "source_title": "示例来源",
        "source_organization": "示例机构",
        "source_type": "research",
        "source_url": None,
        "source_reference": None,
        "source_accessible": False,
        "publication_date": date(2026, 1, 1),
        "evidence_quote": "",
        "risk_flags": ["missing_evidence"],
        "review_status": "pending",
    })

    assert evidence.can_confirm is False
    assert evidence.with_status(ReviewStatus.CONFIRMED).review_status is ReviewStatus.PENDING
```

- [ ] **Step 3: Run the test and verify RED**

Run: `python -m pytest tests/test_domain.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'src.domain'`.

- [ ] **Step 4: Implement domain contracts**

Use string enums and immutable Pydantic models. The critical guardrail must be explicit:

```python
# src/domain.py
from __future__ import annotations
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import StrEnum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class ProjectStage(StrEnum):
    TASK = "task"
    FRAMEWORK = "framework"
    SOURCES = "sources"
    EVIDENCE = "evidence"
    BRIEF = "brief"


class ReviewStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    NEEDS_EDIT = "needs_edit"
    DISCARDED = "discarded"


class SourceType(StrEnum):
    PRIMARY = "primary"
    RESEARCH = "research"
    SECONDARY = "secondary"
    LEAD_ONLY = "lead_only"


class RiskFlag(StrEnum):
    MISSING_EVIDENCE = "missing_evidence"
    INACCESSIBLE_SOURCE = "inaccessible_source"
    MISSING_KEY_FIELD = "missing_key_field"
    DEFINITION_CONFLICT = "definition_conflict"
    VALUE_CONFLICT = "value_conflict"
    POSSIBLY_STALE = "possibly_stale"
    LEAD_ONLY_SOURCE = "lead_only_source"
    SOURCE_BIAS = "source_bias"
    TITLE_CONTENT_MISMATCH = "title_content_mismatch"
    PARSE_FAILED = "parse_failed"


class AccessStatus(StrEnum):
    ACCESSIBLE = "accessible"
    INACCESSIBLE = "inaccessible"
    LOCAL = "local"


class ExtractionStatus(StrEnum):
    PENDING = "pending"
    EXTRACTED = "extracted"
    FAILED = "failed"


class EvidenceCategory(StrEnum):
    COMPANY = "company"
    COMMERCIALIZATION = "commercialization"
    FINANCING = "financing"
    COMPETITION = "competition"
    MARKET = "market"
    SUPPLY_CHAIN = "supply_chain"
    TECHNICAL_PRINCIPLE = "technical_principle"
    HISTORY = "history"
    STANDARD = "standard"


class WorkflowStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ResearchQuestion(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    dimension: str
    question: str
    priority: int = Field(ge=1, le=3)
    approved: bool = False


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SupplementalItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    kind: Literal["file", "url"]
    display_name: str
    reference: str
    byte_size: int | None = None
    extraction_status: ExtractionStatus = ExtractionStatus.PENDING
    warning: str | None = None


class ResearchProject(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    topic: str
    geography: str
    time_range: str
    purpose: str
    focus_questions: tuple[str, ...] = ()
    supplemental_items: tuple[SupplementalItem, ...] = ()
    stage: ProjectStage = ProjectStage.TASK
    framework_confirmed_at: datetime | None = None
    last_plan_workflow_run_id: str | None = None
    last_evidence_workflow_run_id: str | None = None
    last_brief_workflow_run_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class SourceRecord(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    project_id: str
    title: str
    organization: str
    source_type: SourceType
    url: str | None = None
    local_reference: str | None = None
    publication_date: date | None = None
    accessed_at: datetime = Field(default_factory=utc_now)
    access_status: AccessStatus
    extraction_status: ExtractionStatus
    risk_flags: tuple[RiskFlag, ...] = ()
    workflow_run_id: str | None = None


class EvidenceRecord(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    project_id: str
    research_question_id: str
    research_question: str
    source_id: str
    category: EvidenceCategory
    claim: str
    numeric_value: Decimal | None = None
    unit: str | None = None
    geography: str
    period: str
    definition_scope: str
    source_title: str
    source_organization: str
    source_type: SourceType
    source_url: str | None
    source_reference: str | None = None
    source_accessible: bool
    publication_date: date | None
    evidence_quote: str
    risk_flags: tuple[RiskFlag, ...] = ()
    review_status: ReviewStatus = ReviewStatus.PENDING

    @property
    def can_confirm(self) -> bool:
        blocked = {RiskFlag.MISSING_EVIDENCE, RiskFlag.INACCESSIBLE_SOURCE}
        has_reference = bool(self.source_url or self.source_reference)
        return bool(self.evidence_quote.strip() and self.source_accessible and has_reference) and not blocked.intersection(self.risk_flags)

    def with_status(self, status: ReviewStatus) -> "EvidenceRecord":
        if status is ReviewStatus.CONFIRMED and not self.can_confirm:
            return self.model_copy(update={"review_status": ReviewStatus.PENDING})
        return self.model_copy(update={"review_status": status})


class WorkflowCheckpoint(BaseModel):
    model_config = ConfigDict(frozen=True)
    project_id: str
    workflow: Literal["plan", "evidence", "brief"]
    workflow_run_id: str | None = None
    status: WorkflowStatus
    completed_unit_ids: tuple[str, ...] = ()
    error_code: str | None = None
    error_message: str | None = None
    updated_at: datetime = Field(default_factory=utc_now)


class ClaimEvidenceMap(BaseModel):
    model_config = ConfigDict(frozen=True)
    sentence: str
    evidence_ids: tuple[str, ...]


class BriefMode(StrEnum):
    PREVIEW = "preview"
    FORMAL = "formal"


class BriefBundle(BaseModel):
    model_config = ConfigDict(frozen=True)
    project_id: str
    mode: BriefMode
    markdown: str
    claim_evidence_map: tuple[ClaimEvidenceMap, ...]
    created_at: datetime = Field(default_factory=utc_now)
```

Import `Literal` from `typing`. Tests must instantiate every model, reject an invalid enum, and verify two separately created objects receive independent UTC timestamps.

- [ ] **Step 5: Add Streamlit router and empty pages**

`streamlit_app.py` must call `st.navigation` once and execute the selected page:

```python
import streamlit as st

st.set_page_config(page_title="具身智能研究工作台", page_icon="🔎", layout="wide")
page = st.navigation([
    st.Page("app/pages/task_setup.py", title="01 研究需求"),
    st.Page("app/pages/framework.py", title="02 研究框架"),
    st.Page("app/pages/sources.py", title="03 资料来源"),
    st.Page("app/pages/evidence.py", title="04 证据矩阵"),
    st.Page("app/pages/brief.py", title="05 研究简报"),
])
page.run()
```

Each page renders its title and a caption naming the task that will implement the workflow. Do not add fake results.

- [ ] **Step 6: Run tests and lint**

Run: `python -m pytest tests/test_domain.py -q`

Expected: PASS.

Run: `ruff check streamlit_app.py app src tests/test_domain.py`

Expected: `All checks passed!`

- [ ] **Step 7: Commit**

```bash
git add .gitignore .env.example .streamlit requirements.txt requirements-dev.txt streamlit_app.py app src/config.py src/domain.py tests/test_domain.py
git commit -m "feat: scaffold research workbench"
```

---

### Task 2: SQLite Project and Evidence Repository

**Files:**
- Create: `src/storage.py`
- Create: `tests/test_storage.py`
- Create: `data/.gitkeep`

**Interfaces:**
- Consumes: Domain models from Task 1.
- Produces: `WorkbenchRepository(db_path)`, `create_project()`, `save_framework()`, `replace_sources()`, `replace_evidence()`, `review_evidence()`, `save_brief()`, `load_project_snapshot()`, `save_workflow_checkpoint()`, and `latest_workflow_checkpoint()`.

- [ ] **Step 1: Write failing repository tests**

```python
def test_review_state_survives_repository_reload(tmp_path, sample_evidence):
    db = tmp_path / "workbench.sqlite3"
    repo = WorkbenchRepository(db)
    repo.initialize()
    repo.replace_evidence("pr-1", [sample_evidence])
    repo.review_evidence("ev-1", ReviewStatus.CONFIRMED)

    reloaded = WorkbenchRepository(db)
    assert reloaded.list_evidence("pr-1")[0].review_status is ReviewStatus.CONFIRMED
```

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_storage.py -q`

Expected: FAIL because `WorkbenchRepository` does not exist.

- [ ] **Step 3: Implement schema and repository**

Use `sqlite3`, JSON-serialize Pydantic models, enable WAL mode, foreign keys, and explicit transactions. Create tables `projects`, `framework_questions`, `sources`, `evidence`, `briefs`, `workflow_checkpoints`, and `events`. `replace_evidence()` must delete and insert within one transaction; `review_evidence()` must use `EvidenceRecord.with_status()` so blocked records cannot be confirmed. A failed workflow writes its sanitized error and completed unit IDs without deleting prior successful results, so the page can show a retry action from the failed module.

```python
class WorkbenchRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA foreign_keys=ON")
            connection.executescript(SCHEMA_SQL)
```

- [ ] **Step 4: Test rollback behavior**

Add a test that injects a duplicate evidence ID during `replace_evidence()` and asserts the previous rows remain unchanged after the integrity error.

- [ ] **Step 5: Run repository tests**

Run: `python -m pytest tests/test_storage.py -q`

Expected: PASS, including rollback test.

- [ ] **Step 6: Commit**

```bash
git add src/storage.py tests/test_storage.py data/.gitkeep
git commit -m "feat: persist research projects"
```

---

### Task 3: Supplemental Material Validation and Ingestion

**Files:**
- Create: `src/ingestion.py`
- Create: `tests/test_ingestion.py`
- Create: `tests/fixtures/sample.pdf`
- Create: `tests/fixtures/sample.md`
- Modify: `app/pages/task_setup.py`

**Interfaces:**
- Consumes: Uploaded-file objects exposing `.name`, `.size`, and `.read()`.
- Produces: `validate_items(files, urls) -> list[IngestionIssue]`, `extract_material(file) -> SupplementalMaterial`, `select_context(materials, questions, max_chars=80_000) -> str`.

- [ ] **Step 1: Write boundary tests**

Test exactly 5 items passes; 6 fails; `report.docx` fails; a 20 MiB file passes; 20 MiB + 1 byte fails; a scanned PDF with no extractable text returns `parse_failed` instead of raising.

```python
def test_six_supplemental_items_are_rejected(fake_upload):
    files = [fake_upload(f"f{i}.txt", b"x") for i in range(6)]
    issues = validate_items(files, [])
    assert [issue.code for issue in issues] == ["too_many_items"]
```

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_ingestion.py -q`

Expected: FAIL because ingestion functions do not exist.

- [ ] **Step 3: Implement validation, extraction, and chunking**

Define these exact constants:

```python
MAX_ITEMS = 5
MAX_FILE_BYTES = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}
CHUNK_CHARS = 6_000
CHUNK_OVERLAP = 300
MAX_CONTEXT_CHARS = 80_000
```

Extract PDF text page by page with labels `[filename p.N]`. Chunk on paragraph boundaries, then rank chunks by overlap between normalized question terms and chunk terms. Return the highest-ranked chunks without exceeding `MAX_CONTEXT_CHARS`; always include a warning listing omitted chunk count.

- [ ] **Step 4: Wire the research-task form**

Create fields `topic`, `geography`, `time_range`, `purpose`, `focus_questions`, `files`, and `urls`. Default topic to `具身智能`, geography to `中国为主，全球对照`, and keep the user on the page when validation fails. Persist a valid project and supplemental-material metadata, then store its ID with `set_project_id()`.

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_ingestion.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/ingestion.py app/pages/task_setup.py tests/test_ingestion.py tests/fixtures
git commit -m "feat: ingest supplemental research files"
```

---

### Task 4: Typed Dify Client and Workflow Contracts

**Files:**
- Create: `src/dify_client.py`
- Create: `schemas/research_framework.schema.json`
- Create: `schemas/evidence_bundle.schema.json`
- Create: `schemas/brief_bundle.schema.json`
- Create: `scripts/validate_workflows.py`
- Create: `tests/test_dify_client.py`
- Create: `tests/test_schemas.py`
- Create: `tests/fixtures/dify_success.json`
- Create: `tests/fixtures/dify_failure.json`

**Interfaces:**
- Consumes: `DIFY_BASE_URL` and one server-side API key per workflow.
- Produces: `DifyWorkflowClient.run(workflow: WorkflowName, inputs: dict[str, object], user_id: str) -> WorkflowResult`; `WorkflowName = Literal["plan", "evidence", "brief"]`; `DifyWorkflowError` with `code`, `retryable`, and `workflow_run_id`.

- [ ] **Step 1: Write failing client tests with `httpx.MockTransport`**

Cover success, 401 non-retryable failure, 429 retryable failure, 500 retry once then success, malformed output, and a 60-second timeout. Assert API keys never appear in error strings.

```python
def test_500_retries_once_then_returns_result(mock_transport):
    client = DifyWorkflowClient(settings, transport=mock_transport([500, 200]))
    result = client.run("plan", {"topic": "具身智能"}, user_id="test-user")
    assert result.status == "succeeded"
    assert mock_transport.call_count == 2
```

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_dify_client.py -q`

Expected: FAIL because the client does not exist.

- [ ] **Step 3: Implement blocking workflow client**

POST to `{base_url}/workflows/run` with `response_mode="blocking"`, `user`, and `inputs`. Use a 60-second timeout, exponential delays of 0.5 seconds then 1 second, and at most 2 total attempts. Retry only 429, 500, 502, 503, 504, and transport errors. Parse `data.outputs`; reject responses without `data.status == "succeeded"`.

- [ ] **Step 4: Define exact JSON schemas**

Set `additionalProperties: false` at every object level and define these exact required fields:

- `research_framework.schema.json`: root `questions`; every item requires `id`, `dimension`, `question`, `priority`, and `approved`; `dimension` is one of the seven fixed research dimensions, `priority` is integer 1–3, and the array contains 21–42 unique IDs.
- `evidence_bundle.schema.json`: root `sources` and `evidence`. Every source requires `id`, `project_id`, `title`, `organization`, `source_type`, `publication_date`, `access_status`, `extraction_status`, `risk_flags`, and `workflow_run_id`; `url` and `local_reference` are nullable but at least one must be present. Every evidence item requires `id`, `project_id`, `research_question_id`, `research_question`, `source_id`, `category`, `claim`, `numeric_value`, `unit`, `geography`, `period`, `definition_scope`, `source_title`, `source_organization`, `source_type`, `source_url`, `source_reference`, `source_accessible`, `publication_date`, `evidence_quote`, `risk_flags`, and `review_status`; nullable fields remain present with JSON `null`.
- `brief_bundle.schema.json`: root `project_id`, `mode`, `markdown`, and `claim_evidence_map`; `mode` is exactly `preview` or `formal`. Every mapping requires `sentence` and a unique `evidence_ids` array. `markdown` has `minLength: 1`; evidence IDs have `minLength: 1`; empty evidence arrays are permitted only for headings and explicit uncertainty statements and are checked locally in Task 8.

Use the same enum literals as `src/domain.py`. Add parametrized `Draft202012Validator` tests that validate one known-good fixture and reject an extra property, a missing required field, an invalid enum, and a source with neither URL nor local reference. Add a separate local contract test for duplicate IDs because JSON Schema `uniqueItems` does not detect two objects that differ outside the ID field.

- [ ] **Step 5: Add workflow contract validator**

`scripts/validate_workflows.py` loads each exported Dify YAML and asserts exact variable names:

```python
EXPECTED = {
    "research_plan.yml": ({"topic", "geography", "time_range", "purpose", "focus_questions"}, {"framework_json"}),
    "evidence_collection.yml": ({"project_id", "framework_json", "supplemental_context"}, {"sources_json", "evidence_json"}),
    "brief_generation.yml": ({"project_id", "brief_mode", "evidence_json"}, {"brief_json"}),
}
```

- [ ] **Step 6: Run tests**

Run: `python -m pytest tests/test_dify_client.py tests/test_schemas.py -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/dify_client.py schemas scripts/validate_workflows.py tests/test_dify_client.py tests/test_schemas.py tests/fixtures/dify_*.json
git commit -m "feat: add typed Dify workflow client"
```

---

### Task 5: Research Planning Workflow and Framework Review

**Files:**
- Create: `prompts/research_plan.md`
- Create: `workflows/research_plan.yml`
- Modify: `app/pages/task_setup.py`
- Modify: `app/pages/framework.py`
- Create: `tests/test_app.py`

**Interfaces:**
- Consumes: Project task fields; `DifyWorkflowClient.run("plan", ...)`.
- Produces: A confirmed list of `ResearchQuestion`; framework status persisted as `approved=True` before evidence collection is enabled.

- [ ] **Step 1: Save the exact planning prompt**

Save this core prompt in `prompts/research_plan.md`; substitute only the five named input variables and attach `research_framework.schema.json` as structured output:

```text
你是精品 FA 初级分析师的研究规划器。你的任务是拆解问题，不搜索、不回答问题、不估算数字。

研究任务：
- 主题：{{topic}}
- 地域：{{geography}}
- 时间范围：{{time_range}}
- 用途：{{purpose}}
- 用户重点问题：{{focus_questions}}

严格生成以下七个且仅七个维度，每个维度 3–6 个问题：
1. 市场定义与边界
2. 市场规模与 CAGR
3. 产业链与关键环节
4. 竞争格局与标杆公司
5. 技术趋势与能力演进
6. 融资活动与商业化进展
7. 风险、争议与关键假设

规则：
- 用中文输出；每条问题只询问一件事；priority 只能为 1、2、3；approved 初始为 false。
- 明确区分中国与全球，明确区分具身智能、人形机器人和工业机器人；不要默认它们口径相同。
- 市场规模/CAGR 问题必须在问题中包含地域与历史期或预测期；缺失时先提出口径澄清问题，不得自行估算。
- 技术趋势与标杆公司允许全球对照；商业化、融资、产业链以中国为主。
- 保留用户重点问题，但归入最匹配的固定维度；不要添加投资建议、公司推荐或项目 sourcing。
- 只输出符合 research_framework.schema.json 的 JSON，不输出解释、Markdown 或结论。
```

- [ ] **Step 2: Configure the Dify `research-plan` workflow**

Create this node graph in Dify Cloud:

```text
User Input
  → Input Validation IF/ELSE
  → GPT-5.4 mini LLM (reasoning: low, structured output)
  → Output(framework_json)
```

Use five exact inputs: `topic`, `geography`, `time_range`, `purpose`, `focus_questions`. Test once in Dify, export the DSL to `workflows/research_plan.yml`, and create a workflow API key stored only in local Streamlit secrets as `DIFY_PLAN_API_KEY`.

- [ ] **Step 3: Verify the exported contract**

Run: `python scripts/validate_workflows.py workflows/research_plan.yml`

Expected: `research_plan.yml: contract valid`.

- [ ] **Step 4: Write AppTest for framework gating**

Mock the Dify client. Assert evidence navigation/action remains disabled until the user approves every retained question, and that deleting a question persists after rerun.

```python
def test_evidence_collection_disabled_until_framework_confirmed(app_test):
    at = app_test.switch_page("app/pages/framework.py").run()
    assert at.button(key="confirm_framework").disabled is False
    assert at.button(key="start_evidence_collection").disabled is True
```

- [ ] **Step 5: Implement framework page**

Use `st.data_editor` for `dimension`, `question`, `priority`, `approved`; allow row deletion but not arbitrary dimension names. The confirmation button validates at least one question in each of the seven dimensions, saves the framework, records a `framework_confirmed` event, and enables evidence collection. Write a `running` checkpoint before calling Dify and `succeeded` or sanitized `failed` afterward. On failure, keep the task form and any previous framework intact and show `Retry framework generation`.

- [ ] **Step 6: Run tests**

Run: `python -m pytest tests/test_app.py -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add prompts/research_plan.md workflows/research_plan.yml app/pages/task_setup.py app/pages/framework.py tests/test_app.py
git commit -m "feat: approve AI research frameworks"
```

---

### Task 6: Evidence Collection Workflow and Source Review

**Files:**
- Create: `prompts/evidence_extraction.md`
- Create: `workflows/evidence_collection.yml`
- Modify: `app/pages/sources.py`
- Modify: `src/storage.py`
- Modify: `tests/test_storage.py`
- Modify: `tests/test_app.py`

**Interfaces:**
- Consumes: Confirmed framework JSON and selected supplemental context.
- Produces: `SourceRecord[]` and candidate `EvidenceRecord[]`, all initially `review_status="pending"`.

- [ ] **Step 1: Save the evidence extraction prompt**

Save this core prompt in `prompts/evidence_extraction.md`; the workflow supplies one approved question and a list of source documents, then validates against `evidence_bundle.schema.json`:

```text
你是证据提取器，不是研究报告作者。只从提供的来源正文中提取能直接回答研究问题的证据。

项目 ID：{{project_id}}
研究问题：{{research_question_json}}
来源正文与元数据：{{source_documents}}
用户补充材料摘录：{{supplemental_context}}

规则：
- 每条 evidence 只表达一个事实或来源观点；claim 必须能被 evidence_quote 直接支持。
- evidence_quote 必须逐字来自正文并保留最小充分上下文；不得改写为引文。
- 数字必须拆出 numeric_value、unit、geography、period、definition_scope；原文没有的字段用 null 或空字符串，并加入 missing_key_field，不得猜测。
- 找不到直接证据时，返回一条 risk_flags 含 missing_evidence 的候选记录，claim 明确写“未找到可确认的直接证据”，不得补写答案。
- 不合并不同地域、时期或定义口径；同题冲突数值分别保留。
- 政府/监管/标准/论文/公司公告与官网为 primary；公司材料另加 source_bias。
- 披露方法的协会、咨询或研究机构为 research；有编辑审核的主流媒体为 secondary；聚合站、无引用营销页和来源不明内容为 lead_only，并加入 lead_only_source。
- 标题与正文不匹配时加入 title_content_mismatch；无法访问时 source_accessible=false 且加入 inaccessible_source。
- 所有新记录 review_status=pending。source_url 或 source_reference 至少一个存在。
- 只输出符合 evidence_bundle.schema.json 的 JSON，不输出解释、Markdown 或投资结论。
```

- [ ] **Step 2: Configure Tavily in Dify**

Install Dify Marketplace plugin `langgenius/tavily` version 0.1.11, configure its key in Dify, and use `Search` plus `Extract`. For each approved question: generate two Chinese and one English query; return at most 5 results per query; deduplicate by canonical URL before extraction; set `include_raw_content=true`; do not request Tavily AI answers because the product needs source text, not a second synthesized answer.

- [ ] **Step 3: Configure the Dify evidence workflow**

```text
User Input
  → Parse framework JSON
  → Iterate approved questions (parallelism 3)
      → Generate 3 search queries
      → Tavily Search(max_results 5)
      → Canonical-URL dedupe
      → Tavily Extract
      → GPT-5.4 mini structured evidence extraction
  → Merge and global dedupe
  → Output(sources_json, evidence_json)
```

Pass supplemental file excerpts into the extraction node with their `[filename p.N]` labels. Send user-supplied URLs through Tavily Extract even when they were not returned by Search; mark inaccessible URLs without stopping other sources. Export to `workflows/evidence_collection.yml` and store the workflow key as `DIFY_EVIDENCE_API_KEY`.

- [ ] **Step 4: Add idempotency test**

Given the same workflow run ID twice, `replace_sources()` and `replace_evidence()` must leave one logical copy. Store `last_evidence_workflow_run_id` on the project and ignore duplicate completions.

- [ ] **Step 5: Implement source page**

Show title, organization, source role, publication date, URL, access state, and extraction state. Provide filters for inaccessible and lead-only sources. Let users discard a source; discarding a source also marks its evidence records `discarded`.

Show the latest evidence `WorkflowCheckpoint` above the table. If the run failed, retain already persisted sources/evidence, display the sanitized error and completed-question count, and provide `Retry failed questions`; the retry payload contains only approved question IDs absent from `completed_unit_ids`. A successful retry merges by stable source/evidence ID and replaces the checkpoint with `succeeded`.

- [ ] **Step 6: Verify workflow contract and tests**

Run: `python scripts/validate_workflows.py workflows/evidence_collection.yml`

Expected: `evidence_collection.yml: contract valid`.

Run: `python -m pytest tests/test_storage.py tests/test_app.py -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add prompts/evidence_extraction.md workflows/evidence_collection.yml app/pages/sources.py src/storage.py tests/test_storage.py tests/test_app.py
git commit -m "feat: collect traceable research evidence"
```

---

### Task 7: Deterministic Quality Rules and Evidence Review

**Files:**
- Create: `src/quality.py`
- Create: `tests/test_quality.py`
- Modify: `app/pages/evidence.py`
- Modify: `src/storage.py`

**Interfaces:**
- Consumes: Candidate `EvidenceRecord[]` and a `reference_date`.
- Produces: `assess_record(record, reference_date) -> EvidenceRecord`; `detect_value_conflicts(records) -> dict[str, tuple[str, ...]]`; `detect_definition_conflicts(records) -> dict[str, tuple[str, ...]]`; persisted user review decisions.

- [ ] **Step 1: Write failing quality-rule tests**

Cover missing quote, missing URL, missing geography/period/unit/definition for numeric claims, 12-month company staleness, 24-month market staleness, exemption for standards/history, lead-only source, same-question same-definition numeric conflicts, and different-definition non-conflicts.

```python
def test_market_report_older_than_24_months_is_flagged(market_evidence):
    assessed = assess_record(market_evidence, reference_date=date(2026, 8, 10))
    assert RiskFlag.POSSIBLY_STALE in assessed.risk_flags
```

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_quality.py -q`

Expected: FAIL because quality functions do not exist.

- [ ] **Step 3: Implement pure deterministic rules**

Keep rule functions pure and independent of Streamlit/Dify. Numeric conflict grouping key is `(research_question_id, geography, period, unit, definition_scope)`; only different numeric values inside the same key receive `value_conflict`. Definition-conflict grouping key is `(research_question_id, geography, period, unit)`; two or more non-empty `definition_scope` values receive `definition_conflict` but remain separate records. Apply the 12-month rule to `company`, `commercialization`, `financing`, and `competition`; the 24-month rule to `market` and `supply_chain`; exempt `technical_principle`, `history`, and `standard`.

- [ ] **Step 4: Implement evidence matrix UI**

Default sort order: blocked records, conflicts, stale, incomplete, clean pending, confirmed, discarded. Display research question, claim, value/unit, period, source, flags, and status. A detail pane shows full quote, URL, publication date, definition scope, and the reason for every flag. Confirmation calls `with_status()` and shows a blocking message when quote or accessible URL is absent.

- [ ] **Step 5: Record human interventions**

Every edit, confirm, needs-edit, or discard action writes an event with `evidence_id`, previous status, new status, changed fields, and timestamp. Never store API keys or full uploaded documents in event payloads.

- [ ] **Step 6: Run tests**

Run: `python -m pytest tests/test_quality.py tests/test_storage.py tests/test_app.py -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/quality.py src/storage.py app/pages/evidence.py tests/test_quality.py tests/test_storage.py tests/test_app.py
git commit -m "feat: review evidence quality risks"
```

---

### Task 8: Candidate Preview, Confirmed-Evidence Formal Brief, Citation Guardrail, and Exports

**Files:**
- Create: `prompts/brief_generation.md`
- Create: `workflows/brief_generation.yml`
- Create: `src/brief_validation.py`
- Create: `src/exporting.py`
- Create: `tests/test_brief_validation.py`
- Create: `tests/test_exporting.py`
- Modify: `app/pages/brief.py`

**Interfaces:**
- Consumes: For `BriefMode.PREVIEW`, only accessible, directly quoted, non-discarded candidate `EvidenceRecord` objects; for `BriefMode.FORMAL`, only `EvidenceRecord` objects with `review_status="confirmed"`.
- Produces: mode-tagged `BriefBundle`; `validate_brief(bundle, evidence_by_id) -> BriefValidationResult`; `evidence_to_csv(records) -> bytes`; `brief_to_markdown(bundle) -> str`. Preview bundles are non-exportable; formal bundles alone are exportable.

- [ ] **Step 1: Write failing guardrail tests**

Test that every factual sentence maps to at least one allowed evidence ID; unknown IDs fail; headings and explicit uncertainty statements may have zero evidence IDs. For `formal`, pending/discarded IDs fail and a blocked sentence prevents export. For `preview`, any inaccessible, missing-quote, or discarded ID fails; pending IDs are permitted only when the rendered preview shows citations, risk labels, and pending/unconfirmed status. Assert previews have no download/export control and cannot be presented as final.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_brief_validation.py tests/test_exporting.py -q`

Expected: FAIL because validators/serializers do not exist.

- [ ] **Step 3: Implement brief validator and exports**

Use the Dify-provided `claim_evidence_map`; do not try to infer mappings from prose. Reject any mapped ID absent from the allowed evidence dictionary for the bundle mode. `formal` rejects all non-confirmed evidence; `preview` rejects inaccessible, missing-quote, and discarded evidence. CSV columns follow the spec data-model order and use UTF-8 with BOM for Chinese spreadsheet compatibility. Markdown adds a numbered source appendix with stable evidence IDs. Only a validated `formal` bundle is passed to an export serializer or download control.

- [ ] **Step 4: Save brief prompt and configure workflow**

Save this core prompt in `prompts/brief_generation.md` and validate against `brief_bundle.schema.json`:

```text
你是行业研究简报编辑器。唯一可用事实库是 {{evidence_json}}。输出模式是 {{brief_mode}}，其值只能是 `preview` 或 `formal`。

输出结构：
1. 研究范围与口径
2. 核心发现
3. 市场规模与增长
4. 产业链与竞争格局
5. 技术趋势
6. 融资与商业化
7. 风险、争议与证据缺口

规则：
- 不得引入证据记录中没有的事实、数字、公司、因果关系或投资建议。
- 每个事实性句子末尾添加一个或多个稳定证据 ID，格式为 [EV:ev-1]；并在 claim_evidence_map 中逐句重复完全相同的句子与 ID。
- 标题可以没有证据 ID。明确写成“现有可用证据不足以判断……”的不确定性句子可以映射为空数组。
- 对同题冲突值分别陈述来源、地域、时期和 definition_scope，不选边、不求平均；在正文中明确写“口径不可直接比较”或“证据存在冲突”。
- 在所选模式没有可用证据的章节保留标题并写明证据缺口，不补全内容。
- 当 `brief_mode` 为 `preview`：只能使用来源可访问、具有直接 evidence_quote、且未被剔除的候选记录；首行必须标注“待审核、不可导出预览”；每条事实性句子除证据 ID 外还必须展示 pending/unconfirmed 状态和 risk_flags；不得使用“最终”“正式”或任何可交付表述。
- 当 `brief_mode` 为 `formal`：唯一可用记录的 review_status 必须为 `confirmed`；不得显示待审核状态；正式结果可用于导出。
- 只输出符合 brief_bundle.schema.json 的 JSON，不输出 JSON 之外的文字。
```

Configure:

```text
User Input(project_id, brief_mode, evidence_json)
  → GPT-5.4 mini structured brief generation
  → Code node: reject unknown or mode-ineligible evidence IDs
  → Output(brief_json)
```

Export to `workflows/brief_generation.yml` and store its key as `DIFY_BRIEF_API_KEY`.

- [ ] **Step 5: Implement brief page**

Offer a clearly labeled `待审核、不可导出预览` only when at least one candidate record is accessible, has a direct quote, and is not discarded. Its mode is `preview`; it must display the citation, risk labels, and pending/unconfirmed state for every factual sentence, and it has no copy-as-final, download, or export control. Offer `正式简报` generation only when evidence is confirmed. Its mode is `formal`; write workflow checkpoints around either Dify call, and a failure retains the previous validated result and exposes `Retry brief generation`. Run local mode-aware validation before display. If validation fails, show blocked sentences and a “Return to evidence review” action; do not render download buttons. Only if a `formal` result passes may the page offer `研究简报.md` and `证据矩阵.csv` through `st.download_button(on_click="ignore")`.

- [ ] **Step 6: Run tests and workflow validation**

Run: `python scripts/validate_workflows.py workflows/brief_generation.yml`

Expected: `brief_generation.yml: contract valid`.

Run: `python -m pytest tests/test_brief_validation.py tests/test_exporting.py tests/test_app.py -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add prompts/brief_generation.md workflows/brief_generation.yml src/brief_validation.py src/exporting.py app/pages/brief.py tests/test_brief_validation.py tests/test_exporting.py tests/test_app.py
git commit -m "feat: generate evidence-backed briefs"
```

---

### Task 9: Offline Evaluation Harness and 30-Question Benchmark

**Files:**
- Create: `evals/questions.csv`
- Create: `evals/gold/*.json`
- Create: `scripts/run_eval.py`
- Create: `tests/test_eval.py`
- Create: `tests/fixtures/eval_run.json`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: Saved workflow results or an explicitly enabled live `DifyWorkflowClient`.
- Produces: `evals/runs/<timestamp>.json` with question-level judgments and aggregate metrics; process exit 0 only when all acceptance thresholds pass.

- [ ] **Step 1: Create the evaluation dataset**

Add exactly 30 questions: 6 market definition, 6 market size/CAGR, 6 technology trend, 6 supply-chain/competition, and 6 financing/commercialization. Each row contains `question_id`, `category`, `question`, `required_fields`, `severe_error_rules`, and `gold_file`. Each gold JSON contains human reference claims, accepted source URLs, source publication dates, geography, period, unit, and definition scope.

- [ ] **Step 2: Write failing metric tests**

Test these formulas exactly:

```python
evidence_support_rate = supported_claims / total_claims
citation_access_rate = accessible_citations / total_citations
key_field_completeness = complete_numeric_claims / total_numeric_claims
```

Zero denominators return `None`, not 0 or 1, and fail the corresponding threshold with reason `insufficient_sample`.

- [ ] **Step 3: Verify RED**

Run: `python -m pytest tests/test_eval.py -q`

Expected: FAIL because the evaluation runner does not exist.

- [ ] **Step 4: Implement fixture and live modes**

Default command reads saved fixtures and makes no network calls:

```bash
python scripts/run_eval.py --mode fixture --input tests/fixtures/eval_run.json
```

Live mode requires `--confirm-live-cost` and secrets:

```bash
python scripts/run_eval.py --mode live --confirm-live-cost
```

Print question-level failures, aggregate rates, severe-error count, and threshold PASS/FAIL. Write the complete JSON run locally; ignore run files in Git except `.gitkeep`.

- [ ] **Step 5: Run benchmark unit tests**

Run: `python -m pytest tests/test_eval.py -q`

Expected: PASS.

- [ ] **Step 6: Run fixture benchmark**

Run: `python scripts/run_eval.py --mode fixture --input tests/fixtures/eval_run.json`

Expected: all metric calculations match fixture expectations; the command states whether release thresholds pass.

- [ ] **Step 7: Commit**

```bash
git add .gitignore evals scripts/run_eval.py tests/test_eval.py tests/fixtures/eval_run.json
git commit -m "test: add embodied intelligence benchmark"
```

---

### Task 10: User-Test Telemetry and Operations Package

**Files:**
- Create: `src/telemetry.py`
- Create: `tests/test_telemetry.py`
- Create: `docs/user-test-script.md`
- Modify: `src/storage.py`
- Modify: `app/pages/task_setup.py`
- Modify: `app/pages/framework.py`
- Modify: `app/pages/evidence.py`
- Modify: `app/pages/brief.py`

**Interfaces:**
- Consumes: User interactions and stage timestamps.
- Produces: `record_event(project_id, event_name, payload)`, `stage_duration(project_id, stage)`, and a local anonymized CSV export for user-test analysis.

- [ ] **Step 1: Write telemetry privacy tests**

Assert payloads containing keys matching `api_key`, `token`, `secret`, `document_text`, or `evidence_quote` are rejected. Assert user identifiers are session codes such as `UT-01`, not email addresses.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_telemetry.py -q`

Expected: FAIL because telemetry functions do not exist.

- [ ] **Step 3: Implement event recording**

Record `project_created`, `framework_generated`, `framework_confirmed`, `evidence_started`, `evidence_completed`, `evidence_reviewed`, `brief_generated`, `brief_exported`, `task_abandoned`, and `manual_intervention`. Store timestamps in UTC and compute durations from events, never from Streamlit session uptime.

- [ ] **Step 4: Write the exact 45-minute user-test protocol**

`docs/user-test-script.md` contains:

```text
0–5 min: consent, role, recent research task
5–10 min: reconstruct existing workflow and baseline time
10–30 min: complete the standard task without coaching
30–35 min: inspect and correct at least three evidence records
35–40 min: generate/export the brief
40–45 min: trust, usefulness, blocker, and repeat-use questions
```

The standard task is: “为一次内部项目讨论，形成中国具身智能商业化进展的证据底稿，并对照全球技术趋势。” Record completion, time, manual interventions, accepted/edited/discarded evidence, export, and exact repeat-use answer.

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_telemetry.py tests/test_storage.py tests/test_app.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/telemetry.py src/storage.py app/pages/task_setup.py app/pages/framework.py app/pages/evidence.py app/pages/brief.py docs/user-test-script.md tests/test_telemetry.py tests/test_storage.py tests/test_app.py
git commit -m "feat: measure user research sessions"
```

---

### Task 11: CI, Deployment Runbook, and End-to-End Release Gate

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `docs/runbook.md`
- Create: `scripts/smoke_live.py`
- Modify: `README.md`
- Modify: `.gitignore`
- Modify: `tests/test_app.py`
- Create: `tests/fixtures/e2e/market_size.json`
- Create: `tests/fixtures/e2e/technology_trend.json`
- Create: `tests/fixtures/e2e/commercialization.json`

**Interfaces:**
- Consumes: All earlier modules, workflows, tests, and secrets supplied outside Git.
- Produces: reproducible local setup, CI checks, live smoke command, Streamlit Community Cloud deployment instructions, and a release checklist.

- [ ] **Step 1: Add three complete Streamlit AppTest scenarios**

Use fake Dify responses and a temporary SQLite path for three parametrized scenarios: China market size/CAGR with conflicting definitions, global technology trends with a stale-exempt technical source, and China commercialization/financing with a stale company source. In every scenario create a project, approve the seven-dimension framework, load evidence, block one invalid confirmation, confirm one valid record, generate a mapped brief, and assert both download buttons appear. Store the provider fixtures under `tests/fixtures/e2e/` and assert no network request occurs.

- [ ] **Step 2: Add GitHub Actions CI**

On pushes and pull requests to `main`, use Python 3.12, install `requirements-dev.txt`, then run:

```bash
ruff check streamlit_app.py app src scripts tests
python -m pytest --cov=src --cov=app --cov-report=term-missing -q
python scripts/validate_workflows.py workflows
python scripts/run_eval.py --mode fixture --input tests/fixtures/eval_run.json
```

Set a 15-minute job timeout and no provider secrets.

- [ ] **Step 3: Write live smoke script**

Require an explicit workflow selector and validate only one small request. Redact Authorization headers and truncate provider responses in errors. Exit nonzero on schema/guardrail failure.

- [ ] **Step 4: Write runbook**

Document these exact setup gates:

1. Create a Dify Cloud workspace.
2. Configure OpenAI `gpt-5.4-mini` and Tavily plugin 0.1.11 in Dify.
3. Import the three workflow YAML files and create one API key per workflow.
4. Put keys in `.streamlit/secrets.toml`; never commit that file.
5. Run `python -m pytest -q`, workflow validation, fixture eval, and one explicit live smoke.
6. Run locally with `streamlit run streamlit_app.py`.
7. Connect Streamlit Community Cloud to the private GitHub repository, select Python 3.12 and `streamlit_app.py`, and paste secrets in Advanced Settings.
8. Keep the deployed app private during user testing; invite only the 3–5 testers.

- [ ] **Step 5: Run the complete local release gate**

Run:

```bash
ruff check streamlit_app.py app src scripts tests
python -m pytest --cov=src --cov=app --cov-report=term-missing -q
python scripts/validate_workflows.py workflows
python scripts/run_eval.py --mode fixture --input tests/fixtures/eval_run.json
```

Expected: every command exits 0. Record exact counts and benchmark rates in the commit notes; do not claim live-provider quality from fixture tests.

- [ ] **Step 6: Run one live end-to-end scenario**

Run: `python scripts/smoke_live.py --workflow all --confirm-live-cost`

Expected: task → framework → evidence → brief succeeds, every brief factual sentence maps to confirmed evidence, and no secret appears in logs.

- [ ] **Step 7: Commit**

```bash
git add .github/workflows/ci.yml docs/runbook.md scripts/smoke_live.py README.md .gitignore tests/test_app.py tests/fixtures/e2e
git commit -m "chore: add MVP release gate"
```

---

### Task 12: Real-User Results and Portfolio Case Study

**Files:**
- Create: `docs/portfolio-case-study.md`
- Create: `evals/user-tests/summary.csv`
- Modify: `README.md`

**Interfaces:**
- Consumes: Completed sessions from 3–5 target users and the latest live 30-question evaluation result.
- Produces: a truthful case study, anonymized result table, and resume-ready evidence without invented metrics.

- [ ] **Step 1: Conduct at least 3 complete user sessions**

Use `docs/user-test-script.md`. Assign session codes `UT-01` onward. Do not collect names, employer names, emails, confidential deal data, or uploaded client materials in the repository.

- [ ] **Step 2: Export and manually verify anonymized results**

`evals/user-tests/summary.csv` contains only:

```text
session_code,completed,baseline_minutes,assisted_minutes,evidence_confirmed,evidence_edited,evidence_discarded,manual_interventions,brief_exported,would_reuse,top_value,top_blocker
```

Open the CSV and confirm no personally identifying or confidential text exists before staging.

- [ ] **Step 3: Run the live 30-question benchmark**

Run: `python scripts/run_eval.py --mode live --confirm-live-cost`

Expected: a timestamped local result. Copy only aggregate metrics and anonymized failure categories into the case study; do not commit raw provider payloads.

- [ ] **Step 4: Write the case study**

Use this answer-first structure:

1. One-sentence outcome with actual measured values.
2. User and workflow problem.
3. Why evidence-first beat report-first.
4. MVP scope and discarded ideas.
5. AI/data architecture and human checkpoints.
6. Evaluation design and actual results.
7. User-test behavior and actual results.
8. Three most important failure cases and iterations.
9. Remaining risks and next experiment.
10. Resume bullet using only verified numbers.

If any acceptance target is missed, state the miss and the corrective experiment; never replace it with an aspirational number.

- [ ] **Step 5: Update README with verified results**

Add links to the case study and deployed private test app. Report raw sample size alongside any percentages.

- [ ] **Step 6: Final verification**

Run: `python -m pytest -q`

Expected: PASS.

Run: `git diff --check`

Expected: no output and exit 0.

- [ ] **Step 7: Commit**

```bash
git add docs/portfolio-case-study.md evals/user-tests/summary.csv README.md
git commit -m "docs: publish validated MVP case study"
```

## 15-Day Timebox

| Day | Primary outcome |
|---:|---|
| 1 | Task 0: 2–3 problem interviews and baseline gate |
| 2 | Tasks 1–2: foundation, domain contracts, persistence |
| 3 | Task 3: validated supplemental ingestion |
| 4 | Task 4: Dify client and schemas |
| 5–6 | Task 5: planning workflow and framework gate |
| 7–8 | Task 6: Tavily evidence workflow and source page |
| 9 | Task 7: quality engine and evidence review |
| 10 | Task 8: brief guardrail and exports |
| 11 | Task 9: 30-question evaluation harness |
| 12 | Task 10: telemetry and user-test protocol |
| 13 | Task 11: CI, deployment, end-to-end release gate |
| 14–15 | Task 12: 3–5 user sessions, live benchmark, case study |

If the schedule slips, preserve Tasks 1–9 and cut visual polish before cutting evidence traceability, quality rules, or evaluation. The user-test count may finish after Day 15, but the product must not claim validated user value until at least 3 complete sessions exist.

## Manual Account and Cost Checkpoints

- Dify Cloud, Tavily, OpenAI API, and Streamlit Community Cloud accounts require user-owned sign-in and terms acceptance.
- Before the first live call, show the user which provider will incur usage and obtain approval to use their keys.
- Keep Dify workflow keys server-side. The official Dify API guidance warns against exposing workflow keys to clients; Streamlit acts as the server layer.
- Use `gpt-5.4-mini` because current official OpenAI documentation confirms structured outputs, a 400k context window, and a lower-cost mini tier suitable for repeated extraction; availability and billing still depend on the user’s API account.
- Tavily search/extract is the selected Dify plugin because it returns title, URL, publication date when available, and extracted content; the app must still verify accessibility and evidence support independently.
