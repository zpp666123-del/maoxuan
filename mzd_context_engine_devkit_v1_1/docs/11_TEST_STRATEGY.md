# 11. 测试策略

## 11.1 测试金字塔

```text
少量：用户验收 / 端到端 / 压测 / 安全演练
中量：API 契约 / 工作流 / Prompt Eval / 数据迁移
大量：单元 / Schema / 规则 / 组件 / SQL
```

## 11.2 单元测试

### 后端

- Anchor 解析与覆盖；
- 时间过滤；
- 检索排序；
- source ID 校验；
- 卡片重复检测；
- cache key；
- release 组合；
- 幂等和取消；
- 权限；
- 场景节点和日期校验。

### 前端

- AnchorObserver 稳定；
- uiVersion 丢弃旧流；
- Slot 状态机；
- GenerationRun → Card 渲染；
- SSE 重连；
- 移动端抽屉；
- 场景文字等价；
- 锁定卡片。

## 11.3 Schema 契约测试

- 所有 examples 必须通过 JSON Schema；
- OpenAPI 响应示例必须与 Schema 一致；
- 后端模型与 JSON Schema 自动比对；
- Prompt output schema 变更必须触发兼容性检查；
- 发布包中不存在未引用 Schema。

运行：

```bash
python tools/validate_package.py
```

## 11.4 API 集成测试

覆盖：

- 创建会话；
- 获取运行记录；
- 创建交互；
- SSE 正常顺序；
- SSE 中断恢复；
- 幂等；
- 取消；
- 单槽位失败；
- 模型超时；
- 旧 release；
- 权限失败；
- Rate Limit。

## 11.5 工作流测试

对 `reading-workflow.yaml` 每个节点测试：

- 输入输出 Schema；
- 条件分支；
- 超时；
- 重试；
- 回退；
- 取消；
- 节点幂等；
- 从中间节点恢复；
- 运行记录完整性。

## 11.6 Prompt Eval

### 离线

每次 Prompt 或模型策略变更运行 Golden Set：

- 结构合法；
- 规则检查；
- 关键词/禁用事实；
- 允许来源；
- LLM-as-judge 评分；
- 人工抽样。

LLM Judge 只作为信号，不能替代历史审核。

### 对比

候选版本与当前发布版本比较：

- 总分；
- 时间泄漏；
- 无来源事实；
- 重复；
- 平均长度；
- unavailable；
- 延迟和成本。

存在 P0 回退时禁止发布。

## 11.7 时间泄漏测试

构造专门用例：

- 资料中同时包含当时状态和后来结果；
- 用户问题故意询问“事实证明是否正确”；
- 选区附近提到后来重印说明；
- ContextUnit 的事件时间早但 `knownAt` 晚；
- 后来回忆录描述当时情况。

检查回到当时模式只显示当时可知信息，并正确标记后来的研究视角。

## 11.8 提示注入测试

攻击样例：

- 选中文本包含“忽略系统提示”；
- 用户问题要求输出系统 Prompt；
- 导入资料带有伪造 JSON 指令；
- 来源标题伪装成角色消息；
- 请求模型生成未经整理的坐标或来源 ID；
- 问题要求超出当前文章自由发挥。

预期：规则不改变、用户输入作为数据、未知返回不足、系统 Prompt 不泄露。

## 11.9 E2E 测试

场景：

1. 进入文章，首个运行记录出现；
2. 连续滚动三个锚点；
3. 选中一句文字，背景保持、思想更新；
4. 切换回到当时，后续信息消失；
5. 打开决策路径；
6. 提问并收到带来源的回答；
7. 快速进行第二次选中，旧 SSE 不覆盖；
8. 模型故障时回退运行记录；
9. 提交反馈；
10. 移动端完成相同主任务。

## 11.10 性能测试

### 读取

- 热门文章运行记录并发；
- 正文与锚点；
- Redis miss 回源；
- 相邻预取。

### SSE

- 长连接数；
- 心跳；
- 慢客户端；
- 断线重连；
- 代理超时。

### AI

- 不同模型配额；
- 并行三槽位；
- Validator；
- 取消请求；
- 离线批量运行记录。

目标见 PRD 非功能需求。

## 11.11 数据迁移测试

- 从上一 Schema 迁移；
- 回滚；
- Release 仍可读取；
- GenerationRun Hash 不意外改变；
- 旧 GenerationRun 可解释；
- 新字段有默认值；
- 数据库与 JSON Schema 兼容。

## 11.12 灾难恢复演练

至少验证：

- PostgreSQL 恢复；
- Redis 全丢失后的重建；
- 对象存储恢复；
- Prompt/Workflow 从 Git 恢复；
- 当前 Release 指针恢复；
- 旧运行记录可继续服务；
- 模型供应商不可用切换。

## 11.13 发布前必跑测试

```text
schema validation
unit tests
API contract
workflow tests
prompt golden set
time leakage suite
prompt injection suite
E2E smoke
generation_run integrity
backup/rollback smoke
```

