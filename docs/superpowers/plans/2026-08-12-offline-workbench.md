# Offline Research Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local, five-page embodied-intelligence research workbench with SQLite persistence and non-bypassable evidence-review guardrails.

**Architecture:** Streamlit pages call focused application modules in `src/`. Immutable Pydantic contracts and a SQLite repository own business state; quality, brief-selection, mapping, demo fixtures and exports are pure services tested without a running UI.

**Tech Stack:** Python 3.12, Streamlit, Pydantic 2, SQLite, pandas, pytest, Streamlit AppTest, Ruff.

## Global Constraints

- All UI copy is Chinese; only five stages exist: 研究需求、研究框架、资料来源、证据矩阵、研究简报.
- The domain is embodied intelligence, China first with global technical comparison; frameworks contain exactly seven fixed dimensions.
- This offline phase makes no Dify, Tavily, OpenAI, network, upload, telemetry or cloud-deployment calls.
- Use SQLite WAL, foreign keys and explicit transactions; data must survive reopening the same database path.
- Evidence cannot be confirmed without an accessible source, non-empty direct quote and URL or local reference.
- Preview uses eligible pending/needs_edit/confirmed evidence and is explicitly non-exportable; formal uses only confirmed evidence and exports only after sentence mapping validates.
- Risk/status/mode use visible text, not color alone; no credentials, raw uploads or provider payloads are committed.

---

## File Structure

```text
streamlit_app.py
app/pages/{task_setup,framework,sources,evidence,brief}.py
src/{domain,storage,quality,briefs,demo,exporting}.py
tests/{test_domain,test_storage,test_quality,test_briefs,test_exporting,test_app}.py
requirements.txt
requirements-dev.txt
.streamlit/config.toml
.gitignore
```

### Task 1: Domain contracts and quality rules

**Files:** Create `src/domain.py`, `src/quality.py`, `tests/test_domain.py`, `tests/test_quality.py`; create `requirements.txt`, `requirements-dev.txt`.

**Interfaces:** Produces `ReviewStatus`, `RiskFlag`, `Project`, `ResearchQuestion`, `SourceRecord`, `EvidenceRecord`; `eligible_for_preview(evidence) -> bool`, `assess_risks(evidence, today) -> set[RiskFlag]`, `sort_key(evidence) -> tuple[int, str]`.

- [ ] Write tests that prove invalid evidence cannot become confirmed, a 13-month commercialization source is `possibly_stale`, incomplete market records are `incomplete`, and blocked evidence sorts before conflicts.
- [ ] Run `python -m pytest tests/test_domain.py tests/test_quality.py -q`; expect import-collection failure because modules do not exist.
- [ ] Implement string enums, frozen Pydantic models and pure quality helpers; `with_status(CONFIRMED)` retains prior state when confirmation eligibility fails.
- [ ] Re-run the same command; expect all tests pass.
- [ ] Commit domain contracts and quality rules.

### Task 2: Transactional SQLite repository and demo dataset

**Files:** Create `src/storage.py`, `src/demo.py`, `tests/test_storage.py`.

**Interfaces:** Produces `WorkbenchRepository(path)`, `save_project`, `get_project`, `save_questions`, `list_questions`, `save_sources`, `list_sources`, `save_evidence`, `list_evidence`, `set_review_status`, `exclude_source`, `save_checkpoint`; `load_demo_project(repository) -> str`.

- [ ] Write tests for reopening persistence, source-exclusion cascading to `discarded`, failed transactions retaining prior state, and demo data having all seven dimensions plus clean/conflict/stale/incomplete/blocked records.
- [ ] Run `python -m pytest tests/test_storage.py -q`; expect collection failure because repository is missing.
- [ ] Implement normalized schema with `PRAGMA foreign_keys=ON`, `journal_mode=WAL`, transaction context manager and JSON serialization for risk flags; load synthetic anonymous data only.
- [ ] Re-run `python -m pytest tests/test_storage.py -q`; expect all tests pass.
- [ ] Commit storage and demo dataset.

### Task 3: Brief selection, mapping and export safeguards

**Files:** Create `src/briefs.py`, `src/exporting.py`, `tests/test_briefs.py`, `tests/test_exporting.py`.

**Interfaces:** Produces `build_preview(evidence) -> Brief`, `build_formal(evidence) -> Brief`, `validate_sentence_maps(brief, evidence) -> list[str]`, `evidence_csv(evidence) -> bytes`, `formal_markdown(brief) -> str`.

- [ ] Write tests that preview excludes inaccessible/no-quote/discarded records, formal excludes pending records, a missing sentence mapping blocks formal export, and CSV includes status/risk fields.
- [ ] Run `python -m pytest tests/test_briefs.py tests/test_exporting.py -q`; expect collection failure because modules are missing.
- [ ] Implement deterministic Chinese brief sections, citation-bearing sentence maps and serializers; do not expose preview export functions.
- [ ] Re-run the same command; expect all tests pass.
- [ ] Commit brief and export safeguards.

### Task 4: Streamlit five-page workbench

**Files:** Create `streamlit_app.py`, `app/__init__.py`, `app/pages/__init__.py`, `app/pages/task_setup.py`, `app/pages/framework.py`, `app/pages/sources.py`, `app/pages/evidence.py`, `app/pages/brief.py`, `.streamlit/config.toml`, `tests/test_app.py`; modify `.gitignore`.

**Interfaces:** Consumes `WorkbenchRepository`, domain models and pure services. Produces an app where `streamlit_app.py` has radio navigation keys `nav_task`, `nav_framework`, `nav_sources`, `nav_evidence`, `nav_brief` and buttons with stable keys including `load_demo`, `confirm_framework`, `generate_preview`, `generate_formal`.

- [ ] Write AppTest tests for all five page titles, framework confirmation disabled until all retained questions are approved, blocked evidence lacking a direct quote has no confirm action, preview displays non-exportable text, and formal export appears only after validation.
- [ ] Run `python -m pytest tests/test_app.py -q`; expect collection failure because the app does not exist.
- [ ] Implement the minimum page renderers and session-project selection, use repository transactions for all writes, and provide empty/error guidance that states what happened, what was retained and the next action.
- [ ] Re-run `python -m pytest tests/test_app.py -q`; expect all tests pass.
- [ ] Commit the five-page workbench.

### Task 5: Full validation and operator documentation

**Files:** Create `README.md` updates if required; modify test/config files only to fix discovered defects.

- [ ] Run `python -m pytest -q`, `python -m ruff check .`, and `python -m streamlit run streamlit_app.py --server.headless true` with a bounded smoke check.
- [ ] Correct any verified failures using a new failing regression test before the production fix.
- [ ] Review the implementation against every Global Constraint and document the offline-demo startup command in README.
- [ ] Commit verification/documentation changes.
