# 图表索引

图表同时提供：

- `.dot`：Graphviz 可编辑源文件；
- `.mmd`：核心图的 Mermaid 可编辑源文件；
- `.svg`：适合嵌入 Markdown、网页与设计稿；
- `.png`：适合快速预览与分享。

| 编号 | 图表 | 说明 |
|---|---|---|
| 01 | UI 框架 | 原文、三槽位与动态场景的页面结构 |
| 02 | 产品流程 | 从进入文章到滚动、点击、深挖与反馈 |
| 03 | 系统上下文 | 用户、编辑、外部模型与系统边界 |
| 04 | 容器架构 | Web、API、内容服务、AI 编排与数据层 |
| 05 | AI 运行时 | 规划、检索、生成、校验、流式提交与降级 |
| 06 | 交互时序 | 浏览器到各服务的端到端时序 |
| 07 | 内容生产 | 正文导入、锚点、情境包、审核、运行记录与发布 |
| 08 | 数据模型 | 主要领域实体与版本关系 |
| 09 | 部署拓扑 | CDN、应用、Worker、数据与可观测性 |
| 10 | 状态机 | 阅读交互从 idle 到 streaming/commit/fallback |
| 11 | Prompt 层级 | 宪法、规划、槽位、场景、校验与修复 |
| 12 | 发布版本 | Release 对文章、ContextPack、Prompt、Workflow、GenerationRun 的锁定 |

重新渲染 Graphviz：

```bash
bash tools/render_diagrams.sh
```
