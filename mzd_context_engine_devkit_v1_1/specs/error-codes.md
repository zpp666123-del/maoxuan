# 错误码

| 错误码 | HTTP | 可重试 | 说明 |
|---|---:|---:|---|
| ARTICLE_NOT_FOUND | 404 | 否 | 文章不存在或不可见 |
| RELEASE_NOT_FOUND | 404 | 否 | Release 不存在 |
| RELEASE_MISMATCH | 409 | 否 | 文章、锚点与 Release 不一致 |
| ANCHOR_NOT_FOUND | 404 | 否 | 锚点不存在 |
| GENERATION_NOT_READY | 202 | 是 | 运行记录尚未生成 |
| CONTEXT_INSUFFICIENT | 422 | 否 | 情境资料不足 |
| CONTEXT_SOURCE_FORBIDDEN | 403 | 否 | 来源不可用于当前可见范围 |
| INTERACTION_STALE_UI_VERSION | 409 | 否 | 客户端交互版本过期 |
| INTERACTION_CANCELLED | 409 | 否 | 交互已取消 |
| MODEL_TIMEOUT | 504 | 是 | 模型超时 |
| MODEL_UNAVAILABLE | 503 | 是 | 模型不可用 |
| MODEL_OUTPUT_INVALID | 502 | 是 | 模型输出不合法 |
| VALIDATION_TIME_LEAKAGE | 422 | 否 | 时间冻结泄漏 |
| VALIDATION_UNSUPPORTED_CLAIM | 422 | 否 | 具体事实无来源 |
| VALIDATION_SLOT_CONFUSION | 422 | 是 | 槽位语义混淆，可修复 |
| SCENE_DATA_INVALID | 422 | 否 | 场景 ID/日期/坐标不合法 |
| RATE_LIMITED | 429 | 是 | 超出配额 |
| RIGHTS_RESTRICTED | 403 | 否 | 内容权利限制 |
| IDEMPOTENCY_CONFLICT | 409 | 否 | 同一幂等键请求体不同 |
| INTERNAL_ERROR | 500 | 是 | 未分类错误 |

标准错误体见 `docs/08_API_STREAMING.md`。

