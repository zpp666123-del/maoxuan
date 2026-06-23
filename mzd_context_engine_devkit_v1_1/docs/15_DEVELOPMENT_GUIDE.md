# 15. 开发与交付指南

## 15.1 本地要求

建议安装：

- Docker 与 Compose；
- Python 3.11+；
- Node.js LTS（若采用 React/Next.js）；
- PostgreSQL 客户端；
- Graphviz；
- Git。

具体生产版本应由团队安全基线锁定，本包不声称示例版本为最新。

## 15.2 启动演示骨架

```bash
cd starter
cp .env.example .env
make dev
```

打开 `http://localhost:8000`。Starter 后端加载本地语料，SSE 只连接真实大模型；未配置 API 时返回明确失败事件，不提供模拟生成内容。

也可直接：

```bash
cd starter/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 15.3 校验资料包

```bash
python tools/validate_package.py
```

校验：

- 必需文件；
- JSON/YAML；
- 示例对 JSON Schema；
- DOT/SVG/PNG；
- SQL 基础结构；
- Python 语法。

## 15.4 图表

编辑 `diagrams/*.dot` 后运行：

```bash
bash tools/render_diagrams.sh
```

输出同名 SVG 和 PNG。Markdown 文档优先引用 SVG。

## 15.5 推荐仓库结构

```text
apps/
  reader-web/
  admin-studio/
  api/
workers/
  ai-worker/
  content-worker/
packages/
  contracts/
  ui-components/
  workflow-runtime/
  prompt-registry/
  scene-renderers/
infra/
  migrations/
  compose/
  deploy/
content/
  article-packs/
docs/
```

本资料包可放入 `docs/architecture-kit/`，Schema 和 Prompt 建议迁移到可由代码直接读取的共享包。

## 15.6 编码约定

- API 与数据字段用 `camelCase`；
- 数据库字段用 `snake_case`；
- ID 前缀可读：`art_`、`av_`、`anc_`、`cu_`、`src_`、`rel_`、`int_`；
- 时间使用 ISO 8601 和 UTC；
- 历史日期允许精度字段，不强制伪造完整日期；
- 所有枚举由 Schema 统一定义；
- 业务错误使用错误码，不依赖文案判断；
- Prompt 不散落在业务代码中；
- Workflow 不在 HTTP 控制器中硬编码；
- 模型响应先进入适配层和 Validator。

## 15.7 Git 与版本

建议：

- 主干开发或短分支；
- PR 必须关联需求 ID；
- Schema/Prompt/Workflow 变更单独标记；
- Commit 使用清晰前缀：`feat:`、`fix:`、`content:`、`prompt:`、`schema:`、`infra:`；
- Release Tag 同时记录应用、内容 release 和 Prompt bundle。

## 15.8 API 开发

契约先行：

1. 修改 JSON Schema / OpenAPI；
2. 更新 example；
3. 运行契约测试；
4. 实现后端；
5. 生成或更新前端类型；
6. E2E。

不要先改接口实现后补文档。

## 15.9 Prompt 开发

1. 创建 draft 版本；
2. 明确任务与输出 Schema；
3. 加入至少 5 个失败用例；
4. 运行 Golden Set；
5. 对比发布版本；
6. 内容审核；
7. 发布 Prompt Bundle；
8. 绑定新的 Release 或动态试验组。

生产环境不允许直接修改已发布 Prompt 文本。

## 15.10 内容代码化

文章和 ContextPack 可同时保存在数据库和可审查的导出文件中：

```text
content/article_demo/
  article.json
  context-pack.json
  sources.json
  generation-runs/
  quality-report.json
```

数据库是运行主源，Git 导出用于审查、备份、差异和迁移。导入导出需保证 ID 稳定。

## 15.11 环境变量

见 `starter/.env.example`。生产应至少配置：

```text
DATABASE_URL
REDIS_URL
OBJECT_STORAGE_*
MODEL_GATEWAY_URL
MODEL_GATEWAY_KEY
PROMPT_BUNDLE_VERSION
WORKFLOW_VERSION
LOG_LEVEL
SENTRY/OTEL settings
SESSION_SECRET
ADMIN_OIDC settings
```

密钥不进入代码、Prompt、日志或前端构建。

## 15.12 联调顺序

1. 接 Article/Anchor API；
2. 接 Interaction 创建与真实 SSE；
3. 配置真实 OpenAI-compatible 模型；
4. 接单槽位生成；
5. 接三槽位并行与 Validator；
6. 接设置页 API 管理；
7. 接反馈与监控；
8. 接内容工作台发布。

不要在 UI、数据和模型三层都未稳定时同时联调。

## 15.13 代码评审清单

- 是否绕过 Schema；
- 是否把模型结果直接展示；
- 是否把用户输入放入系统 Prompt；
- 是否忘记 releaseId/uiVersion；
- 是否引入新的具体事实字段却没有来源；
- 是否在滚动路径调用模型；
- 是否有超时、取消和回退；
- 是否记录可观测字段；
- 是否增加测试；
- 是否影响内容审核或权利。

## 15.14 交付物

每个里程碑交付：

- 可部署镜像；
- migration；
- OpenAPI/Schema；
- Prompt/Workflow bundle；
- 内容 release；
- 测试报告；
- 质量报告；
- 监控仪表盘；
- 回滚说明；
- 用户演示脚本。
