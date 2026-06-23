# 14. 研发路线、Epic 与 Backlog

## 14.1 参考团队

最小可行团队：

- 1 产品/项目负责人；
- 1 产品设计/前端；
- 1 后端/架构；
- 1 AI 工程；
- 1 内容编辑/研究；
- 1 兼职历史审核；
- 1 兼职测试/运维。

角色可以兼任，但内容审核与发布决策不能完全由模型承担。

## 14.2 阶段路线

### 阶段 0：协议与可点击真实运行骨架（1–2 周）

目标：团队对产品形态达成一致。

交付：

- UI 槽位 Schema；
- Interaction Event；
- GenerationRun；
- SSE 真实大模型事件流；
- 本地真实语料加载；
- 10 个示例锚点；
- 固定三槽位和两种场景的交互原型。

退出条件：产品、内容和研发都能用同一套对象描述需求，并能看到真实模型失败或成功的流式状态。

### 阶段 1：阅读快路径（2–3 周）

交付：

- 文章、段落、锚点 API；
- 前端 Reader；
- AnchorObserver；
- 真实流式运行记录读取；
- 相邻预取；
- 三槽位状态机；
- 时间线/决策路径基础组件；
- 阅读会话。

退出条件：配置真实 API 后可完整阅读一篇文章；未配置时只显示明确错误，不提供伪生成内容。

### 阶段 2：内容工作台与 ContextPack（3–4 周）

交付：

- 导入；
- 锚点编辑；
- ContextUnit；
- Source；
- Anchor Link；
- AI 候选提取；
- 运行记录批量生成任务；
- 审核状态和发布。

退出条件：内容人员可独立完成示例文章情境包。

### 阶段 3：AI 实时编排（3–4 周）

交付：

- Prompt/Workflow Registry；
- Planner；
- Retriever；
- 三槽位生成器；
- Model Gateway；
- Validator/Repair；
- SSE 语义块；
- 运行记录和动态缓存。

退出条件：点击、选中和模式切换可稳定更新必要槽位。

### 阶段 4：质量、场景和体验（2–3 周）

交付：

- Golden Set；
- 时间泄漏和注入测试；
- 真实场景数据；
- 移动端；
- 无障碍；
- 反馈；
- 质量报表；
- 性能优化。

退出条件：达到 PRD 发布阈值。

### 阶段 5：首篇发布与复盘（1–2 周）

交付：

- 首篇文章发布；
- 小规模用户测试；
- 反馈修订；
- 运行与成本报告；
- 第二篇文章加工估算；
- v1.2 路线。

## 14.3 Epic

### EPIC-A：Canonical Reader

- A1 文章与 release；
- A2 段落和锚点；
- A3 阅读位置；
- A4 当前锚点算法；
- A5 运行记录加载；
- A6 响应式与无障碍。

### EPIC-B：Context UI

- B1 背景卡；
- B2 处境卡；
- B3 思想卡；
- B4 Slot 状态机；
- B5 来源抽屉；
- B6 模式切换；
- B7 卡片锁定。

### EPIC-C：Scene Renderer

- C1 Scene Schema；
- C2 Timeline；
- C3 Decision；
- C4 Map（P1）；
- C5 Relations（P1）；
- C6 文本等价说明。

### EPIC-D：ContextPack Studio

- D1 文章导入；
- D2 锚点编辑；
- D3 Unit 编辑；
- D4 Source；
- D5 Link Matrix；
- D6 场景编辑；
- D7 Gap；
- D8 审核发布。

### EPIC-E：AI Orchestration

- E1 事件规范化；
- E2 Planner；
- E3 Retriever；
- E4 Prompt Registry；
- E5 Slot Generator；
- E6 Validator；
- E7 Repair；
- E8 Scene Planner；
- E9 Model Gateway；
- E10 Run persistence。

### EPIC-F：Streaming & Session

- F1 Reading Session；
- F2 SSE；
- F3 uiVersion；
- F4 Cancel；
- F5 reconnect；
- F6 dynamic cache。

### EPIC-G：Quality & Operations

- G1 Golden Set；
- G2 Prompt Eval；
- G3 feedback；
- G4 observability；
- G5 audit；
- G6 security；
- G7 backup/rollback；
- G8 cost report。

## 14.4 P0 User Stories

### US-001 阅读首屏

作为读者，我进入文章后希望正文和首个情境运行记录快速出现，以便马上开始阅读。

验收：正文可见后运行记录 P95 在目标内；模型故障不影响。

### US-002 锚点切换

作为读者，我滚动到新论证段时希望解释随之变化，但不要频繁闪动。

验收：使用锚点、防抖、最小更新和相邻预取。

### US-003 选中深挖

作为读者，我选中一句话后希望系统重点更新思想分析，并只在必要时更新处境。

验收：Planner 输出符合矩阵；背景通常保持。

### US-004 回到当时

作为读者，我希望隐藏后来结果，从当时可知信息理解判断。

验收：timePolicy 由检索层和 Validator 双重执行。

### US-005 内容加工

作为编辑，我希望将资料拆成情境单元并关联锚点，以便系统稳定生成内容。

验收：不写代码即可完成导入、编辑、关联、预览。

### US-006 发布

作为发布者，我希望发布的是明确版本组合，并能快速回滚。

验收：Release 绑定全部版本，缓存预热后原子切换。

### US-007 质量追踪

作为审核者，我希望从任何卡片看到来源和生成版本，以便修订。

验收：卡片有 sourceRefs，Run 可查询。

## 14.5 技术任务拆分

### Sprint 0

- 建库与 migration；
- JSON Schema；
- OpenAPI；
- SSE 真实模型流；
- 前端框架；
- CI 校验；
- 本地语料样例。

### Sprint 1

- Article/Paragraph/Anchor；
- Release；
- GenerationRun；
- Reader；
- Context Cards；
- Timeline/Decision；
- E2E 首屏。

### Sprint 2

- ContextPack CRUD；
- Source/Entity/Place；
- Link Matrix；
- 审核；
- 运行记录生成任务；
- Admin 权限。

### Sprint 3

- Orchestrator；
- Planner；
- Retriever；
- Model Gateway；
- Prompt Registry；
- SSE；
- Validator；
- Run。

### Sprint 4

- Prompt Eval；
- Feedback；
- Observability；
- Security；
- Load test；
- Mobile；
- Release runbook。

## 14.6 Definition of Ready

一个功能进入开发前必须有：

- 用户价值；
- 输入输出；
- Schema/API；
- UI 状态；
- 权限；
- 异常和降级；
- 埋点；
- 验收用例；
- 是否影响 Prompt/Workflow/ContextPack。

## 14.7 Definition of Done

- 代码与文档；
- 单元和契约测试；
- 日志、指标和错误码；
- 权限；
- 正常、异常、降级路径；
- 评测或内容审核；
- staging 验证；
- 可回滚；
- CHANGELOG。

## 14.8 首篇文章选择标准

选择：

- 问题意识明确；
- 有清晰历史背景和处境；
- 论证结构完整；
- 有可视化空间；
- 篇幅适中；
- 可获得足够高质量背景资料；
- 不依赖复杂版本校勘即可开始。

不要仅按“最著名”选择。原型更需要能验证框架的文章。
