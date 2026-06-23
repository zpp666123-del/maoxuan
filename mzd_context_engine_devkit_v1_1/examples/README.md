# 真实语料样例

样例只用于校验 API、Schema、SSE 与固定三槽位契约。正文 ID 与段落 ID 使用静火版本本地语料的命名方式；完整正文由 `Selected-Works-of-Mao-Zedong-JingHuo-version-main` 目录加载，不在样例里复制全集。

- `mzd_article_sample.json`：文章、段落和锚点样例；
- `mzd_context_pack_sample.json`：来源、实体、ContextUnit 和链接样例；
- `mzd_interaction_sample.json`：文本选中事件；
- `mzd_planner_output_sample.json`：最小更新计划；
- `mzd_generation_run_sample.json`：真实大模型流式运行记录样例。

运行 `python tools/validate_package.py` 校验。
