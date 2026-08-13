# Research Terminal UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the offline Streamlit workbench into a polished investment-banking-style research terminal with richer status, KPI, risk, filtering, and brief qualification surfaces.

**Architecture:** Keep the existing five-page Streamlit entrypoint and SQLite/domain services. Add a small UI presentation module for shared theme, status calculations, and reusable terminal components; keep all calculations derived from repository records and keep evidence guards in `src/briefs.py` and `src/domain.py`.

**Tech Stack:** Python 3.12, Streamlit 1.61, Pydantic 2, SQLite, pytest, Streamlit AppTest, Ruff.

## Global Constraints

- Keep exactly five pages: 研究需求、研究框架、资料来源、证据矩阵、研究简报.
- Use deep navy background, warm-white panels, muted gold accent, and visible text alongside any color-coded state.
- No external network calls, new persistence fields, credentials, raw uploads, or provider payloads.
- Existing SQLite persistence and evidence confirmation/preview/formal/export guardrails must remain unchanged.
- New KPI, charts, tables, and filters derive only from existing repository project/source/evidence records.
- Preview remains non-exportable; formal output remains confirmed-evidence-only and sentence-map validated.

---

### Task 1: Shared terminal theme and project status metrics

**Files:**
- Create: `src/ui.py`
- Modify: `streamlit_app.py`
- Test: `tests/test_ui.py`

**Interfaces:**
- `project_metrics(evidence, sources) -> dict[str, int|float]`
- `risk_breakdown(evidence) -> dict[str, int]`
- `render_terminal_header(project, current_page, metrics) -> None`
- `render_kpi_row(metrics) -> None`

- [ ] Write failing tests for status counts, accessible-source percentage, risk buckets, and header labels.
- [ ] Run `.venv/bin/python -m pytest tests/test_ui.py -q`; expect missing-module failure.
- [ ] Implement deterministic metric helpers and shared CSS/component renderers with visible labels.
- [ ] Run the focused tests; expect pass.
- [ ] Commit `feat: add research terminal UI primitives`.

### Task 2: Upgrade the project dashboard and framework page

**Files:**
- Modify: `streamlit_app.py`
- Test: `tests/test_app.py`

**Interfaces:**
- Dashboard shows project scope cards, seven-dimension coverage, risk summary, review progress, and next action.
- Framework shows progress KPI, dimension cards, and explicit confirmation blocker while preserving existing edit/save actions.

- [ ] Add AppTest assertions for `项目状态`, `审核进度`, `研究范围`, and `七维框架覆盖`.
- [ ] Run the focused AppTest; expect failure because labels are absent.
- [ ] Refactor the page rendering into terminal sections and add stable UI keys without changing repository contracts.
- [ ] Run focused AppTest; expect pass.

### Task 3: Upgrade sources, evidence, and brief pages

**Files:**
- Modify: `streamlit_app.py`
- Test: `tests/test_app.py`

**Interfaces:**
- Sources page exposes access/role filters and compact source rows.
- Evidence page exposes risk/status filters, KPI counts, and review queue while retaining confirm guard.
- Brief page shows preview/formal qualification panels, counts, blocking copy, and export controls only for valid formal output.

- [ ] Add AppTest assertions for `风险队列`, `来源可访问率`, `候选预览`, `正式简报`, and `不可导出`.
- [ ] Run focused AppTest; expect failure because labels are absent.
- [ ] Implement filters as view-only operations and update visible cards/tables; do not mutate evidence on filtering.
- [ ] Run focused AppTest; expect pass.

### Task 4: Visual QA, docs, and full verification

**Files:**
- Modify: `.streamlit/config.toml`, `README.md`, `tests/test_app.py`

- [ ] Add deep-navy theme variables and update README with the terminal UI behavior.
- [ ] Run `.venv/bin/python -m pytest -q`, `.venv/bin/python -m ruff check .`, and `git diff --check`.
- [ ] Run Streamlit AppTest and local server smoke check; inspect visible page text at desktop width.
- [ ] Commit `feat: polish research terminal workbench`.

