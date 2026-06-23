# 17. 组件系统与交互风格

## 选型

前端 Starter 采用 Web Components 友好的组件体系，样式参考 Web Awesome / Shoelace：

- Web Awesome 是 MIT 许可的开源 Web Components 组件库；
- Shoelace 已转向 Web Awesome，但仍说明其组件可跨框架、可 CDN 使用、可通过 CSS 定制；
- 当前 Starter 没有前端构建链，因此不直接引入大型 npm 前端框架，而是以 Web Awesome 的组件语义建立本地 token、按钮、徽章、面板、dialog、timeline 和 action strip。

地图能力采用本地化 Leaflet 组件作为 Starter 地图包。地图打开时先使用文章和语义变量即时渲染大地图，关键词可立即加入地图；后台 `map_context` workflow 作为“AI 更新地图变量”的增强入口，完成后通过 `map.variables.committed` SSE 事件提交变量层，而不是阻塞首个地图视图。默认开启“进入文章后自动准备全篇与地图”，配置 API 后会在后台预热全篇总览和地图变量。

## 设计原则

- 正文是主画布，AI 与 Agent 是可追踪的解释层。
- 所有探索入口必须是真按钮，不能只是装饰节点。
- 全篇总览和地图变量默认后台预热；地图先由本地地图组件和文章变量即时生成；时间线、人物、事件和插图通过点击 workflow 增强，不提供静态伪答案。
- 没有模型 API 时返回失败事件，正文仍可阅读。
- 图标使用统一 SVG 图标，不使用 emoji。

## 当前组件

- `topbar`：macOS/iPadOS 风格阅读器工具栏，包含文章选择、运行状态、搜索、笔记、字体和设置入口；
- `reading-stage`：中心正文、锚点、选区分析和提问；
- `tool-dock`：左右竖向图标+名字工具栏，左侧保留阅读 workflow（全篇、时间线、人物、事件），右侧只放辅助工具（地图、插图、关系、转折），避免重复入口抢阅读注意力；
- `tool-dialog`：锚点、情境、Agent 输出和地图工作台的统一弹窗；
- `search-panel` / `note-panel`：顶部搜索、笔记是真交互入口；搜索即时定位正文段落，笔记按文章本地保存；字体入口直接打开设置里的正文字号；
- `map-workbench`：Leaflet 大地图、语义地图变量列表、关键词即时加入、`map.variables.committed` 刷新和 AI 更新入口；
- `agent-panel`：agent/subagent 队列与 workflow artifact。

## 后续扩展

- 将本地 token 映射到 Web Awesome CSS custom properties；
- 有地图 API key 或真实坐标后，把 Leaflet 变量层升级为真实底图和地理编码；
- 为 `illustration_prompt` 增加真实图像模型配置和生成结果持久化；
- 将 SQLite workflow artifact 迁移到 PostgreSQL。
