# 08. API、SSE 与前后端协议

## 8.1 协议原则

- REST 用于读取文章、创建会话、创建交互和后台编辑；
- SSE 用于服务器向阅读端渐进推送真实大模型输出；
- 阅读端只保留 `framework_stream`；
- 所有写请求支持 `Idempotency-Key`；
- 阅读接口绑定 `releaseId`；
- 所有动态事件包含 `interactionId` 和 `uiVersion`；
- 模型输出必须进入背景、处境、思想三个固定槽位。

完整 OpenAPI 见 `specs/openapi.yaml`。

## 8.2 公共阅读 API

### 获取文章列表

```http
GET /api/v1/articles?collection=mzd&status=published
```

### 获取文章及正文

```http
GET /api/v1/articles/{articleId}?releaseId={releaseId}
```

返回文章元数据、段落和锚点，不返回未发布 ContextUnit。

### 创建阅读会话

```http
POST /api/v1/reading-sessions
```

```json
{
  "releaseId": "rel_mzd_jinghuo_local",
  "articleId": "art_mzd_001",
  "anchorId": "anc_mzd_001_001",
  "mode": "framework_stream",
  "client": {"device": "desktop", "locale": "zh-CN"}
}
```

### 提交交互并启动大模型流

```http
POST /api/v1/reading-sessions/{sessionId}/interactions
Idempotency-Key: <uuid>
```

请求遵循 `interaction-event.schema.json`。

响应立即返回：

```json
{
  "interactionId": "int_01",
  "status": "accepted",
  "streamUrl": "/api/v1/interactions/int_01/events",
  "pollUrl": "/api/v1/interactions/int_01",
  "uiVersion": 7
}
```

### 查询交互结果

```http
GET /api/v1/interactions/{interactionId}
```

用于 SSE 断开后的恢复。

### 获取大模型 API 设置摘要

```http
GET /api/v1/settings/llm
```

响应不会回传 API key：

```json
{
  "baseUrl": "https://api.openai.com/v1",
  "model": "gpt-4.1-mini",
  "hasApiKey": true,
  "apiKeySource": "runtime",
  "temperature": 0.2
}
```

### 保存大模型 API 设置

```http
PUT /api/v1/settings/llm
```

```json
{
  "baseUrl": "https://api.openai.com/v1",
  "model": "gpt-4.1-mini",
  "apiKey": "sk-...",
  "temperature": 0.2
}
```

`apiKey` 只写入后端运行时内存，不会通过读取接口回显。生产环境应替换为密钥管理服务。

## 8.3 SSE 端点

```http
GET /api/v1/interactions/{interactionId}/events
Accept: text/event-stream
Last-Event-ID: 12
```

### 事件序列

```text
interaction.accepted
plan.committed
slot.started
slot.block *
slot.committed
interaction.completed
```

异常：

```text
slot.unavailable
interaction.failed
interaction.cancelled
heartbeat
```

### 示例

```text
id: 1
event: interaction.accepted
data: {"interactionId":"int_01","uiVersion":7}

id: 2
event: plan.committed
data: {"framework":"fixed_three_slot_context_reader","updateSlots":["background","situation","thought"],"keepSlots":[]}

id: 3
event: slot.started
data: {"slot":"background"}

id: 4
event: slot.block
data: {"slot":"background","kind":"draft","text":"标题：..."}

id: 5
event: slot.committed
data: {"slot":"background","payload":{...}}

id: 6
event: interaction.completed
data: {"status":"completed","uiVersion":7}
```

## 8.4 错误格式

```json
{
  "error": {
    "code": "MODEL_CONFIGURATION_MISSING",
    "message": "缺少真实大模型密钥或模型名。",
    "requestId": "req_...",
    "retryable": false,
    "details": {
      "required": ["LLM_API_KEY", "LLM_MODEL"]
    }
  }
}
```

错误码分类：

- `AUTH_*`
- `ARTICLE_*`
- `RELEASE_*`
- `CONTEXT_*`
- `INTERACTION_*`
- `MODEL_*`
- `VALIDATION_*`
- `RATE_LIMIT_*`
- `INTERNAL_*`

## 8.5 幂等与取消

- 创建交互使用 `Idempotency-Key`；
- 同键在 24 小时内返回同一 interaction；
- 客户端新交互可调用：

```http
POST /api/v1/interactions/{interactionId}/cancel
```

- 服务端取消后发送 `interaction.cancelled`；
- 已提交卡片不会回滚，但前端基于 `uiVersion` 决定是否展示。

## 8.6 管理 API

### 导入文章

```http
POST /api/v1/admin/articles/import
```

支持 multipart 文件或 JSON。

### 编辑锚点

```http
PUT /api/v1/admin/article-versions/{versionId}/anchors
```

### 创建/修改 ContextUnit

```http
POST /api/v1/admin/context-packs/{packVersionId}/units
PUT  /api/v1/admin/context-units/{unitId}
```

### 链接锚点

```http
POST /api/v1/admin/context-packs/{packVersionId}/links
```

### 发布

```http
POST /api/v1/admin/articles/{articleId}/releases
```

发布请求必须指定正文、ContextPack、Prompt 和 Workflow 版本，不允许隐式使用“最新”。

## 8.7 权限

- 阅读公开文章：无需登录；
- 保存进度/笔记：registered_reader；
- 编辑：content_editor；
- 历史审核：historical_reviewer；
- 思想审核：thought_reviewer；
- 发布：publisher；
- Prompt/Workflow：ai_admin；
- 系统配置：system_admin。

RBAC 见 `specs/rbac.yaml`。

## 8.8 兼容性

- URL 包含 `/v1/`；
- 新增可选字段向后兼容；
- 删除或改变语义需要新 API 大版本；
- Schema 有独立 `$id` 与版本；
- 前端发送 `X-Client-Schema-Version`；
- 服务端可返回最低支持版本。
