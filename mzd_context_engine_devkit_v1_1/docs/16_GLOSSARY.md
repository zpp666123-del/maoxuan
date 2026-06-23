# 16. 术语表

| 术语 | 定义 |
|---|---|
| 选定版本 / Canonical Edition | 项目当前采用的唯一正文版本；不表示学术上的绝对定本 |
| ArticleVersion | 某次导入并冻结的正文版本 |
| Paragraph | 稳定 ID 的自然段 |
| Anchor | 由相邻若干段组成的完整阅读情境范围 |
| ContextPack | 围绕一篇文章整理的结构化历史情境包 |
| ContextUnit | 事件、人物状态、约束、争论、选项、概念、地点、结果等最小情境对象 |
| ContextLink | ContextUnit 与 Anchor 的角色、相关度和槽位提示关系 |
| Source | 支持正文或背景具体事实的轻量资料记录 |
| 历史背景 | 当前问题形成之前的重要事件和变化 |
| 当时处境 | 写作时点正在面对的难题、力量、约束、信息和选项 |
| 思想与推理 | 正文从观察和判断走向方法与行动原则的论证过程 |
| Scene | 地图、时间线、关系图或决策路径的声明式数据 |
| GenerationRun | 某锚点和模式下，经审核发布的默认三卡与场景 |
| Fast Path | 滚动时读取运行记录，不调用实时模型 |
| Deep Path | 点击、选中、提问等主动交互触发的 AI 工作流 |
| Prompt Registry | 管理提示词版本、Schema、测试和发布状态的注册表 |
| Workflow Registry | 管理任务节点、分支、超时、回退和版本的注册表 |
| Planner | 决定本次最小更新范围的规划器 |
| Retriever | 从 ContextPack 中选取相关资料的检索器 |
| Validator | 对结构、来源、时间、槽位语义和事实支持进行检查 |
| Semantic Block Streaming | 经过局部校验后按摘要、要点等语义块流式提交，而非裸 Token |
| Time Freeze | 按文章写作时点过滤当时不可知信息的模式 |
| Release | 正文、ContextPack、Prompt、Workflow 和运行记录的不可变发布组合 |
| GenerationRun | 一次 AI 编排的输入、版本、来源、模型、校验和输出记录 |
| Golden Set | 人工定义期望与禁区的固定评测用例集 |
| Gap | 资料、关联、来源或场景存在的内容缺口任务 |

