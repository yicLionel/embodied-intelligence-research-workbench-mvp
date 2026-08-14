# 分阶段 GitHub 发布与 README Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完善可运行 MVP 的 README，并将既有离线、终端 UI、在线研究和稳定性迭代按版本节点快进推送到 GitHub。

**Architecture:** 不改变应用代码和运行时架构。README 作为仓库入口，引用当前已存在的 Streamlit 入口、`src/` 模块、测试套件和配置模板；Git 发布保留既有提交历史，按预先确定的历史提交顺序逐步更新 `codex/offline-workbench` 远端分支，并创建对应标签。

**Tech Stack:** Markdown; Git; Python 3.12; Streamlit; pytest; Ruff; GitHub remote `origin`。

## Global Constraints

- 发布源必须是 `.worktrees/codex-offline-workbench` 的 `codex/offline-workbench` 分支。
- README 只描述当前分支已实现或已配置的能力，不承诺未实现的账号、部署、PPT 或投资决策功能。
- 密钥只通过环境变量或 Streamlit Secrets 读取，不得写入 README 示例的真实值或提交到 Git。
- 版本节点按 `1967e60`、`2ad4266`、`4b695bd`、`40e3f33`、最终 README 提交的顺序快进推送。
- 自动化检查不得调用真实 Tavily、Dify 或 OpenAI 服务。
- 推送前必须检查工作区、验证测试/ruff 输出，并确认远端分支不会被非快进覆盖。

---

### Task 1: 完成 README 内容

**Files:**
- Modify: `README.md`
- Reference: `streamlit_app.py`, `src/online_research.py`, `src/domain.py`, `src/storage.py`, `src/quality.py`, `src/briefs.py`, `src/exporting.py`, `requirements.txt`, `requirements-dev.txt`, `.env.example`

**Interfaces:**
- Consumes: 当前 MVP 的 Streamlit 入口、provider 配置和测试命令。
- Produces: 一份可从仓库根目录直接执行的中文 README，包含运行、配置、测试、架构、边界和版本索引。

- [ ] **Step 1: Verify all README claims against source files**

Run:

```bash
rg -n "page_title|DIFY_|TAVILY_|APP_DB_PATH|def |class |pytest|ruff" streamlit_app.py src requirements*.txt .env.example
```

Expected: every command, environment variable, module name and user-visible workflow used by README has a matching source or configuration reference.

- [ ] **Step 2: Write the README sections**

Include these exact section responsibilities:

```text
项目定位 → 当前状态 → 核心工作流 → 产品原则 → 功能与边界
→ 技术架构 → 目录结构 → 本地运行 → 在线配置
→ 测试与质量检查 → 迭代版本 → 文档 → 安全与限制
```

Use the existing startup commands:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/streamlit run streamlit_app.py
```

Describe both paths explicitly:

```text
无 provider 密钥：侧栏选择“装载演示研究”，浏览离线演示。
配置 TAVILY_API_KEY：运行实时网络检索；DIFY_* 为可选增强工作流。
```

- [ ] **Step 3: Review README for unsupported promises and secret leakage**

Run:

```bash
rg -n "(sk-|tvly-|api[_-]?key\s*[:=]\s*[^$`{])|自动投资|无人审核" README.md
```

Expected: no real secret values and no wording that claims autonomous investment decisions; review any placeholder-like wording manually.

- [ ] **Step 4: Commit README changes**

```bash
git add README.md docs/superpowers/specs/2026-08-14-versioned-github-release-readme-design.md docs/superpowers/plans/2026-08-14-versioned-github-release-readme.md
git commit -m "docs: publish versioned MVP README"
```

### Task 2: Run local verification

**Files:**
- Test: `tests/`
- Check: `README.md`

**Interfaces:**
- Consumes: Task 1 README and the existing test suite.
- Produces: fresh evidence that application tests, lint checks and README references pass.

- [ ] **Step 1: Run the complete test suite**

```bash
.venv/bin/python -m pytest -q
```

Expected: exit code 0 and no failed tests.

- [ ] **Step 2: Run Ruff**

```bash
.venv/bin/ruff check .
```

Expected: exit code 0 and no Ruff errors.

- [ ] **Step 3: Run the README reference check**

```bash
for path in streamlit_app.py src requirements.txt requirements-dev.txt .env.example docs/discovery-interviews.md outputs/2026-08-10-embodied-intelligence-research-workbench-design.md; do test -e "$path"; done
```

Expected: exit code 0; every path linked from README exists in the release branch.

### Task 3: Create local release tags

**Files:**
- Git refs only: `v0.1.0-offline`, `v0.2.0-terminal`, `v0.3.0-online`, `v0.3.1-fallback`, `v0.4.0-readme`

**Interfaces:**
- Consumes: existing historical commits and the verified final README commit.
- Produces: annotated tags that identify the five approved release checkpoints.

- [ ] **Step 1: Confirm the historical commits are ancestors in order**

```bash
git merge-base --is-ancestor 1967e60 2ad4266
git merge-base --is-ancestor 2ad4266 4b695bd
git merge-base --is-ancestor 4b695bd 40e3f33
git merge-base --is-ancestor 40e3f33 HEAD
```

Expected: all commands exit 0.

- [ ] **Step 2: Create annotated tags**

```bash
git tag -a v0.1.0-offline 1967e60 -m "Offline research workbench MVP"
git tag -a v0.2.0-terminal 2ad4266 -m "Research terminal UI"
git tag -a v0.3.0-online 4b695bd -m "Online research workflow"
git tag -a v0.3.1-fallback 40e3f33 -m "Provider fallbacks and resilience"
git tag -a v0.4.0-readme HEAD -m "Documented runnable MVP release"
```

Expected: `git tag --list 'v0.*'` lists exactly the five release tags, unless an identical tag already exists and is verified before reuse.

### Task 4: Push release checkpoints to GitHub

**Files:**
- Remote refs only: `origin/codex/offline-workbench` and the five release tags.

**Interfaces:**
- Consumes: verified local branch, tags, and authenticated remote access.
- Produces: a GitHub branch that advances only by fast-forward through each approved version.

- [ ] **Step 1: Inspect remote state before pushing**

```bash
git remote get-url origin
git ls-remote --heads origin codex/offline-workbench
git ls-remote --tags origin 'refs/tags/v0.*'
```

Expected: remote URL resolves and any existing remote commit is either absent or an ancestor of the local release history.

- [ ] **Step 2: Push branch checkpoints in order**

```bash
git push origin 1967e60:refs/heads/codex/offline-workbench
git push origin 2ad4266:refs/heads/codex/offline-workbench
git push origin 4b695bd:refs/heads/codex/offline-workbench
git push origin 40e3f33:refs/heads/codex/offline-workbench
git push -u origin codex/offline-workbench
```

Expected: each push is a fast-forward update; no force push is permitted.

- [ ] **Step 3: Push tags**

```bash
git push origin v0.1.0-offline v0.2.0-terminal v0.3.0-online v0.3.1-fallback v0.4.0-readme
```

Expected: GitHub exposes all five tags and the final branch points to the verified README commit.

- [ ] **Step 4: Verify remote refs**

```bash
git ls-remote --heads origin codex/offline-workbench
git ls-remote --tags origin 'refs/tags/v0.*'
```

Expected: branch and tags resolve to the intended commits; record the resulting hashes in the handoff.
