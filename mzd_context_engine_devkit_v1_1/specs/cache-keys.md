# 缓存键与失效

## 文章正文

```text
article:{releaseId}:document
article:{releaseId}:anchor:{anchorId}
```

正文缓存只缓存规范正文和锚点结构，不缓存 AI 解释内容。

## 实时交互

```text
interaction:{interactionId}:state
interaction:{interactionId}:events
idempotency:{actorKey}:{idempotencyKey}
```

AI 输出以 interaction/run 为单位追踪。系统不得用缓存内容冒充新的实时大模型结果；如需复用历史运行记录，必须在 UI 和审计字段中明确标识来源。

## 会话

```text
session:{sessionId}
```

## 失效规则

- ContextPack 变更不删除当前 Release 缓存；
- 发布新 Release 后预热正文缓存，再切换公共指针；
- Prompt/Workflow 变更只有绑定新 Release 才影响后续实时运行；
- Redis 丢失后可从 PostgreSQL 和本地语料目录重建正文与运行状态。
