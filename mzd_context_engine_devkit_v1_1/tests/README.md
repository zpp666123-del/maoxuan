# 测试资产

本目录补充规范文档中的测试策略，重点覆盖本产品最容易出错的四类问题：

1. **槽位语义串位**：背景、处境、思想写成同一段摘要；
2. **后见信息泄漏**：把写作之后的结果当成当时已知条件；
3. **资料越界**：模型引用 ContextPack 以外的具体事实；
4. **交互竞态**：旧 `uiVersion` 的流式结果覆盖新页面状态。

文件说明：

- `prompt-eval-cases.yaml`：Prompt 与 Workflow 评估用例；
- `golden/`：可人工审核的标准答案样例；
- `contract/`：JSON Schema、OpenAPI、SSE 与前后端契约测试说明。

完整校验：

```bash
python tools/validate_package.py
```
