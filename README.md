# Embodied Intelligence Research Workbench

面向精品 FA 实习生和初级分析师的具身智能行业研究工作台。

产品将公开网络搜索与用户补充材料转化为可追溯的证据矩阵，在人工确认后生成结构化行业研究简报。首发范围聚焦中国市场的商业化、融资和产业链，并以全球技术趋势和标杆公司作为对照。

## 当前状态

- 阶段：离线可演示 MVP 已实现；研究终端视觉与审核概览已升级，真实 Dify/Tavily/OpenAI 接入待后续配置
- 目标周期：2–3 周
- 实现方式：低代码 AI 工作流，人工质检兜底
- 验证方式：30 题离线评测集、3 个端到端场景、3–5 名目标用户测试

## 产品原则

1. 先证据，后写作。
2. 每条关键结论必须能回到原始证据、来源日期和统计口径。
3. 数字或口径冲突并列展示，不由 AI 擅自选择答案。
4. 没有可访问来源的结论不能进入最终简报。
5. 自动化重复整理工作，保留人的范围确认、事实审核和商业判断。

## 文档

- [MVP 产品设计规格](outputs/2026-08-10-embodied-intelligence-research-workbench-design.md)
- [离线实现规格](docs/superpowers/specs/2026-08-12-offline-workbench-design.md)
- [实施计划](docs/superpowers/plans/2026-08-12-offline-workbench.md)

## 本地运行

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/streamlit run streamlit_app.py
```

在侧栏选择“装载演示研究”即可浏览完整的离线演示流程。演示资料是合成数据，不是实时研究结果。

界面采用精品投行研究终端风格：顶部项目状态带、审核/风险 KPI、来源可访问率、风险优先证据队列，以及候选预览和正式简报的资格面板。所有筛选仅改变视图，不会绕过证据审核门禁。

## 首版非目标

- 项目 sourcing 与公司推荐
- 多行业通用模板
- 完整账号、权限和多人协作系统
- 自动生成精美 PPT
- 无人审核的投资结论
