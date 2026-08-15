# 云端 Dify 搭建指南（正式接入）

本文档说明如何把本项目的两个 Dify Workflow 正式接入 `cloud.dify.ai`，并把 API key 配置到项目里，最终用验证脚本跑通。

涉及的文件都在 `dify/` 目录：

| 文件 | 用途 |
| --- | --- |
| `evidence-workflow.dsl.yml` | 证据提取 workflow（对应 `DIFY_EVIDENCE_API_KEY`） |
| `brief-workflow.dsl.yml` | 正式简报 workflow（对应 `DIFY_BRIEF_API_KEY`） |
| `verify_dify.py` | 用真实 key 校验两个 workflow 输出契约的脚本 |

---

## 1. 两个 workflow 是什么

代码 `src/online_research.py` 里与 Dify 对接的契约：

### 1.1 证据提取 workflow（Evidence）

- **输入**（start 变量）：`topic`、`geography`、`time_range`、`questions`、`sources`
  - `questions` / `sources` 类型为 `json_object`，**值必须是对象**：应用发送的是 `{"items": [...]}`（数组包在 `items` 字段里），workflow 内的「截断并组装输入」代码节点负责解包。不要在调用端直接传数组——Dify 运行时对 json_object 变量校验「must be a dict」。
- **输出**（end 变量）：`evidence`，JSON 数组，每条记录字段：
  `dimension / claim / source_url / evidence_quote / geography / period / unit / definition_scope / category / risk_flags`
- **流程**：截断并组装输入（解包 items）→ LLM 抽取 → 解析 JSON → 输出
- 应用侧消费：`run_online_research()` 里 `DifyWorkflowClient.run(...)` → `workflow.outputs.get("evidence")` → `_evidence_from_dify()`

### 1.2 正式简报 workflow（Brief）

- **输入**：`topic`、`geography`、`time_range`、`evidence`
  - `evidence` 类型为 `json_object`，值必须是对象：应用发送 `{"items": [已确认证据...]}`，LLM 提示词按 `items` 数组取用。
- **输出**：`markdown`（正式简报 Markdown 文本）
- **流程**：LLM 基于已确认证据生成简报 → 输出
- 应用侧消费：`generate_brief_with_dify()`，读取 `outputs.markdown`

> `DIFY_PLAN_API_KEY` 是预留的规划 workflow 配置，当前版本由本地代码生成七维框架，**暂不需要**搭建。

---

## 2. 前置条件

1. 浏览器打开 <https://cloud.dify.ai> 并登录（你已有账号）。
2. 在「设置 → 模型供应商」确认**至少配置了一个可用模型**（OpenAI / DeepSeek / 通义千问 / Kimi 等均可）。导入的 DSL 默认指向 `gpt-4o-mini`，导入后可在 LLM 节点重新选择你账号里已有的模型。

---

## 3. 方式 A：导入 DSL（推荐）

对两个文件各执行一次：

1. 进入 **工作室（Studio）** → 点右上角 **创建空白应用**。
2. 选择 **工作流编排（Workflow）** 类型。
3. 在弹窗里选择 **导入 DSL 文件**，上传 `dify/evidence-workflow.dsl.yml`。
   - 若版本不被接受，报错提示版本太新：把文件顶层 `version: "0.7.0"` 和 `workflow.version: "0.7.0"` 改为 `"0.6.0"` 后重新导入。
4. 同样步骤导入 `dify/brief-workflow.dsl.yml`。
5. 应用名会自动取 DSL 里的名字（「具身智能证据提取」「具身智能正式简报」），可自行改名。

### 导入后必须做的三件事

1. **重新选择模型**：进入应用 → 点 LLM 节点 → 在「模型」处选择你账号里**已配置**的模型（默认 `gpt-4o-mini` 未必在你的账号里可用）。
2. **确认节点联通**：证据提取应用应有「开始 → 截断并组装输入 → 证据提取 LLM → 解析 JSON → 结束」；简报应用应有「开始 → 简报生成 LLM → 结束」。确保没有红叉。
3. **发布**：点右上角 **发布**。未发布的应用无法被 API 调用。

---

## 4. 方式 B：手动搭建（备选，仅当导入失败）

### 4.1 证据提取应用

创建 **Workflow** 应用，按下表配置：

| 节点 | 配置要点 |
| --- | --- |
| 开始 | 变量：`topic`(段落)、`geography`(单行)、`time_range`(单行)、`questions`(json_object)、`sources`(json_object)，全部必填。⚠️ 变量类型不能选 `json`，Dify 运行时只认 `json_object`（UI 里显示为「JSON 对象」） |
| 代码节点（截断并组装输入） | Python3；入参 `topic/geography/time_range/questions/sources` 分别取自开始节点；`questions`/`sources` 是 `{"items": [...]}` 包装的对象，先解包 `items`（容错兼容直接传数组）；questions 取前 20 条、sources 取前 30 条，`raw_content` 截断到 4000 字符、`content` 截断到 1200 字符，组装为 JSON 字符串；输出 `payload`(string) |
| LLM（证据提取） | 温度 0.1；系统提示：只使用 sources 内容、每条证据需直接引文 `evidence_quote`、按 questions 维度组织、输出唯一合法 JSON `{"evidence":[...]}`、`category` 限 `market/technology/commercialization/supply_chain/industry`、`risk_flags` 限 `blocked/conflict/possibly_stale/incomplete/missing_evidence`；用户提示引用 `topic/geography/time_range/payload` |
| 代码节点（解析 JSON） | Python3；入参 `llm_text` 取 LLM 输出；剥离 markdown 代码块标记后 `json.loads`，容错取首尾大括号；输出 `evidence`(array[object]) |
| 结束 | 输出变量名必须是 **`evidence`**，取值来自解析节点的 `evidence` |

### 4.2 正式简报应用

| 节点 | 配置要点 |
| --- | --- |
| 开始 | 变量：`topic`(段落)、`geography`(单行)、`time_range`(单行)、`evidence`(json_object)，全部必填。⚠️ 变量类型不能选 `json`，Dify 运行时只认 `json_object` |
| LLM（简报生成） | 温度 0.3；系统提示：只用输入证据、按七维固定章节组织、数字标注地域/时期/单位/口径、冲突并列呈现、每条结论注明「（来源：标题｜URL｜发布日期）」，输出专业简体中文 Markdown，**禁止输出思考过程或 `<think>` 标签**；用户提示引用 `topic/geography/time_range/evidence` |
| 代码节点（清洗简报） | Python3；入参 `llm_text` 取 LLM 输出；用正则剥离 `<think>...</think>` 块与 `<!--...-->` 注释（DeepSeek 等推理模型会在正文里夹带思考内容），压缩多余空行；输出 `markdown`(string) |
| 结束 | 输出变量名必须是 **`markdown`**，取值来自「清洗简报」节点的 `markdown` |

> ⚠️ 结束节点的输出变量名是硬契约：应用代码按 `evidence` / `markdown` 精确读取，改名会导致验证失败。
>
> ⚠️ **节点 ID 不能包含连字符**：Dify 1.16 运行时（graphon）的模板正则只匹配 `{{#节点ID.变量#}}`，其中节点 ID 只能是字母/数字/下划线（`[a-zA-Z0-9_]{1,50}`）。带 `-` 的节点 ID（如 `start-123`）会导致 LLM 提示词里的变量不被替换、按字面量传给模型。手动搭建时请让 Dify 自动生成的节点 ID 保持原样，提示词里用变量选择器插入变量，不要手敲 ID。

完成后同样要**选择模型并发布**。

---

## 5. 获取 API key

对每个应用：

1. 进入应用 → 左侧 **访问 API**。
2. 在 **API 密钥** 处点 **创建密钥**，复制 `app-xxxx` 形式的密钥。
3. 证据提取应用的 key → `DIFY_EVIDENCE_API_KEY`；简报应用的 key → `DIFY_BRIEF_API_KEY`。

---

## 6. 把 key 配置到项目

两种方式任选其一（推荐 secrets，应用默认读取）：

**方式一：`.streamlit/secrets.toml`**（`.gitignore` 已排除）

```toml
DIFY_BASE_URL = "https://api.dify.ai/v1"
DIFY_EVIDENCE_API_KEY = "app-xxxx"
DIFY_BRIEF_API_KEY = "app-xxxx"
```

**方式二：环境变量**（应用不会自动读 `.env`，需显式加载）

```bash
cp .env.example .env
# 编辑 .env，填入 DIFY_EVIDENCE_API_KEY / DIFY_BRIEF_API_KEY
set -a; source .env; set +a
```

不要把真实 key 提交进 Git。

---

## 7. 验证

```bash
python3 dify/verify_dify.py            # 验证所有已配置的 workflow
python3 dify/verify_dify.py --json     # 机器可读输出
```

脚本会：

- 复用应用自己的 `DifyWorkflowClient` 和配置读取逻辑（环境变量 → secrets.toml 回退）；
- 用三条约 10 行的合成来源调用证据提取 workflow，校验 `evidence` 数组及每条记录的字段契约；
- 用两条已确认的合成证据调用简报 workflow，校验 `markdown` 输出非空；
- 退出码：`0` 全部通过 / `1` 有失败 / `2` 未配置任何 key。

预期输出形如：

```
[evidence] ✅ 通过  status=succeeded
    证据条数: 4  run_id: xxx
[brief] ✅ 通过  status=succeeded
    markdown 长度: 1240  run_id: xxx
```

---

## 8. 在应用里端到端跑通

```bash
.venv/bin/streamlit run streamlit_app.py
```

1. 侧栏 **创建在线研究项目**，填主题/地域/时间范围/用途后保存；
2. **研究框架**页全部问题批准；
3. **资料来源**页点「启动检索」（需要 `TAVILY_API_KEY`）；
4. **证据矩阵**页应看到 Dify 结构化后的候选证据（而不是纯 Tavily 摘录 fallback）；
5. **研究简报**页：确认证据后生成候选预览，再生成正式简报 —— 配置了 `DIFY_BRIEF_API_KEY` 时，正式简报文案由 Dify 生成，失败自动回退本地 Markdown。

---

## 9. 故障排查

| 现象 | 原因与处理 |
| --- | --- |
| `Dify HTTP 401` | key 错误，或应用未点「发布」。检查 `app-` 前缀与发布状态。 |
| `Dify HTTP 404` | 应用已被删除，或 `DIFY_BASE_URL` 写错（云上应为 `https://api.dify.ai/v1`）。 |
| `Dify HTTP 400`，报 `VariableEntity type` 校验错误 | 开始节点的 JSON 类变量类型写成了 `json`。Dify 运行时只认 `json_object`：进开始节点把 `questions`/`sources`/`evidence` 变量类型改为「JSON 对象」后重新发布（或重新导入修正后的 DSL）。 |
| `Dify HTTP 400`，报 `xxx in input form must be a dict` | `json_object` 变量只接受对象，不接受数组。应用与验证脚本发送的是 `{"items": [...]}`；如果你手工调用时直接传了数组，改成对象包装即可。 |
| workflow 成功但 `evidence` 为 0 条 / 简报开头出现 `<think>` 或 `<!--dify-*-reasoning-->` | LLM 是 DeepSeek 等**推理模型**，思考块混进了输出。两种处理：①（推荐）LLM 节点改用非推理模型（`deepseek-chat`、`gpt-4o-mini` 等）；② 确保「解析 JSON」/「清洗简报」代码节点已剥离 `<think>` 块（重新导入修正后的 DSL）。 |
| LLM 收到的提示里是字面量 `{{#...node...#}}`，没有被替换 | 节点 ID 含连字符导致 graphon 模板正则匹配失败。用 Dify UI 的变量选择器重新插入变量，或重新导入修正后的 DSL（节点 ID 已改为纯字母数字）。 |
| `model not found` / 运行报模型错误 | LLM 节点指向的模型在你账号未配置。进应用重选模型再发布。 |
| 输出缺少 `evidence` / `markdown` | 结束节点输出变量名不对，或流程没连到结束节点。对照第 4 节检查。 |
| `evidence` 数组为空 | 合成来源太短或 LLM 判定无证据；可加大来源正文长度重试。 |
| 请求超时（默认 60s） | 证据提取处理 30 条来源可能超时：把 `ONLINE_RESEARCH_TIMEOUT` 调大到 120–180 再试。 |
| 导入报版本不支持 | 把 `version` 从 `"0.7.0"` 改为 `"0.6.0"` 重新导入。 |
| 导入报缺少模型供应商 | 先在「设置 → 模型供应商」安装并配置至少一个模型（LLM 节点用到的 provider 需要可用），再导入。 |

---

## 10. 安全提示

- 云端 Dify 会处理你发送的网页内容和证据数据。使用真实客户/交易材料前，先完成组织内部的安全与合规评估（与 README「安全与数据边界」一致）。
- workflow 内部不保存数据；证据仍以本地 SQLite 为最终存储，人工审核与导出门禁不变。
