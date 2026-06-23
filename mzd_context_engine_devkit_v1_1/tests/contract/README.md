# 契约测试清单

## JSON Schema

- 所有 `examples/*.json` 必须通过对应 Schema；
- 额外字段默认拒绝；
- ID 前缀、枚举、数量和文本长度必须生效；
- 相对 `$ref` 必须可解析；
- Planner 必须满足槽位覆盖和不重叠业务不变量。

## OpenAPI

- OpenAPI YAML 可解析；
- 所有本地 `$ref` 文件存在；
- REST 请求/响应与 JSON Schema 同源；
- 交互创建返回 `interactionId`，SSE 通过该 ID 订阅；
- 所有阅读请求绑定 `releaseId`。

## SSE

- `eventId` 单调递增；
- 重连支持 `Last-Event-ID`；
- 每个事件携带 `interactionId` 与 `uiVersion`；
- `slot.started → slot.block* → slot.committed|slot.unavailable` 顺序合法；
- 旧 `uiVersion` 事件不得提交到当前 UI；
- `interaction.completed|failed|cancelled` 为终态；
- Token 碎片不得直接呈现，必须为语义块。

## 数据一致性

- ContextPack 中的 `sourceIds/entityIds/placeIds` 必须存在；
- AnchorContextLink 的锚点和 ContextUnit 必须存在；
- 时间冻结模式不得检索 `after_writing` 单元；
- 场景节点只能引用本次已检索并审核的数据；
- Release 锁定的所有版本必须存在且状态可发布。

## 推荐工具

- Python：`jsonschema`、`pytest`、`httpx`；
- API：Schemathesis 或 Dredd（团队可选）；
- 前端：Vitest + Playwright；
- 负载：k6；
- Prompt Eval：自建 Golden Set runner，输出逐维评分与差异报告。
