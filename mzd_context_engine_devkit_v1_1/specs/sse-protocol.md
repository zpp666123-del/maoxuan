# SSE 语义块流式协议

版本：`1.1`

## 1. 目标

在固定槽位中提供“正在生成”的即时反馈，同时避免未经校验的 Token 直接进入界面。服务端按语义块与完整对象提交，前端以 `slot.committed` 和 `scene.committed` 为最终真相。

## 2. 连接

```http
GET /api/v1/interactions/{interactionId}/events
Accept: text/event-stream
Cache-Control: no-cache
Last-Event-ID: 12
```

服务端响应：

```http
Content-Type: text/event-stream; charset=utf-8
Cache-Control: no-cache, no-transform
Connection: keep-alive
X-Accel-Buffering: no
```

## 3. 公共字段

每条 data JSON 至少携带：

```json
{
  "interactionId": "int_mzd_001",
  "uiVersion": 7,
  "timestamp": "2026-06-18T00:00:00Z"
}
```

SSE `id` 单调递增。前端使用 `Last-Event-ID` 重连。

## 4. 事件

下面的 interaction 事件服务于正文三槽位上下文生成。工具弹窗内的 agent workflow 使用同一 SSE 基础格式，并额外支持 `workflow.*`、`artifact.*`、`image.*` 与 `map.variables.committed`。

### `interaction.accepted`

```json
{
  "interactionId": "int_mzd_001",
  "uiVersion": 7,
  "status": "accepted"
}
```

### `plan.committed`

```json
{
  "updateSlots": ["situation", "thought"],
  "keepSlots": ["background"],
  "sceneType": "decision",
  "timePolicy": "freeze_at_article_date"
}
```

前端仅对 updateSlots 显示加载状态。

### `slot.started`

```json
{"slot":"situation"}
```

### `slot.block`

用于感知速度，不作为最终缓存：

```json
{
  "slot": "situation",
  "kind": "summary",
  "index": 0,
  "text": "当前最紧迫的问题是……"
}
```

`kind`：`headline`、`summary`、`point`、`uncertainty`。

### `slot.committed`

```json
{
  "slot": "situation",
  "payload": {"slot":"situation", "status":"ready", "headline":"...", "summary":"...", "points":[], "sourceIds":[], "anchorIds":[], "generatedBy":{}}
}
```

payload 必须通过 `ui-card.schema.json`。

### `slot.unavailable`

```json
{
  "slot": "background",
  "reasonCode": "CONTEXT_INSUFFICIENT",
  "message": "当前情境包不足以可靠补充新的背景。",
  "keepPrevious": true
}
```

### `scene.started`

```json
{"sceneType":"decision"}
```

### `scene.committed`

payload 通过 `scene-payload.schema.json`。

### `warning`

```json
{
  "code": "SEMANTIC_VALIDATOR_SKIPPED",
  "message": "已使用确定性校验完成本次低风险更新。"
}
```

警告通常不直接展示给普通用户，可记录到调试面板。

### `interaction.completed`

```json
{
  "status": "completed",
  "updatedSlots": ["situation", "thought"],
  "sceneType": "decision",
  "resultUrl": "/api/v1/interactions/int_mzd_001"
}
```

### `interaction.failed`

```json
{
  "error": {
    "code": "MODEL_OUTPUT_INVALID",
    "message": "本次动态分析未能形成可靠结果。",
    "retryable": true
  }
}
```

### `interaction.cancelled`

```json
{"reason":"superseded_by_newer_ui_version"}
```

### `heartbeat`

每 15–25 秒：

```json
{"serverTime":"2026-06-18T00:00:20Z"}
```

### `map.variables.committed`

仅用于 `map_context` workflow。前端先用本地 Leaflet 组件和文章变量即时渲染地图；该事件到达后原子替换 AI 变量层，并保留用户手动添加的关键词点。

```json
{
  "workflowId": "wf_001",
  "uiVersion": 9,
  "workflow": "map_context",
  "target": {"targetType":"place", "label":"地图语境", "sourceIds":["p_mzd_001_0001"]},
  "variables": [
    {
      "id": "ai_map_abc123",
      "label": "广州",
      "description": "作为文章语义地图中的地点变量",
      "sourceIds": ["p_mzd_001_0001"],
      "lat": 35.8,
      "lng": 104.2,
      "weight": 1,
      "kind": "地点"
    }
  ],
  "generatedBy": {"kind":"real_llm_map_variables"}
}
```

## 5. 顺序与并行

- `interaction.accepted` 必须第一；
- `plan.committed` 在任何 slot 事件前；
- 不同槽位可交错；
- 某槽位的 `started` 在它的 block/committed 前；
- 一个槽位最多一个 committed；
- scene committed 通常在至少一个 slot committed 后；
- completed 最后；
- cancelled/failed 后不得继续提交内容。

## 6. 前端处理

1. 校验 `interactionId`；
2. 若 `uiVersion != currentUiVersion`，丢弃；
3. 对 event id 去重；
4. block 写入临时 partial state；
5. committed 原子替换并清理 partial；
6. 断线后自动重连；
7. 超过重连次数后查询 resultUrl；
8. 旧内容在 committed 到达前保持可见。

## 7. 代理与缓冲

生产反向代理需关闭 SSE 缓冲；连接超时大于任务上限；心跳避免空闲断开。不要对 SSE 启用普通 CDN 缓存或响应压缩缓冲。

## 8. 示例

完整交互负载样例见 `examples/mzd_generation_run_sample.json`；运行时事件流由真实大模型请求实时产生，不维护静态 SSE 文本运行记录。
