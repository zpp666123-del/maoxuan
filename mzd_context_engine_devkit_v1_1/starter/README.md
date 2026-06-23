# 可运行实时大模型骨架

此骨架只保留一种实现路径：

- 固定原文 + 背景/处境/思想三槽位；
- 用户进入、点击段落、选中文字或提问后创建交互；
- 后端调用真实 OpenAI-compatible 大模型流式接口；
- 页面设置中可添加或调整 API Base URL、模型、API Key 和 temperature；
- SSE 将模型输出实时填入预制框架；
- uiVersion 防旧流覆盖。

没有配置真实大模型密钥时，系统会返回 `interaction.failed`，不会使用伪生成或预生成答案兜底。文章正文来自工作区同级目录 `Selected-Works-of-Mao-Zedong-JingHuo-version-main`，后端会按七卷 Markdown 文件自动生成文章列表、段落 ID 和阅读锚点。

如需改用其他位置的语料目录：

```bash
set MZD_CORPUS_DIR=D:\path\to\Selected-Works-of-Mao-Zedong-JingHuo-version-main
```

## 大模型 API 配置

可以在页面右上角“设置”中添加 API，也可以让后端读取以下变量：

```bash
export LLM_API_KEY="你的密钥"
export LLM_MODEL="你的模型名"
export LLM_BASE_URL="https://api.openai.com/v1"
```

也兼容：

```bash
export OPENAI_API_KEY="你的密钥"
export OPENAI_MODEL="你的模型名"
export OPENAI_BASE_URL="https://api.openai.com/v1"
```

`LLM_BASE_URL` / `OPENAI_BASE_URL` 可省略，默认使用 `https://api.openai.com/v1`。

页面设置保存到后端运行时内存；API Key 不会在读取设置时回显。重启服务后请重新设置，生产环境应替换为密钥管理服务。

## Docker 启动

```bash
cp .env.example .env
make dev
```

打开：`http://localhost:8000`

## 本地 Python 启动

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

后端自动服务相邻 `web/` 目录。

## 接入真实实现时替换

- `app/orchestrator.py` → Workflow Runtime；
- 内存 `INTERACTIONS` → PostgreSQL/Redis；
- 静态前端 → 正式 Reader Web；
- 当前 OpenAI-compatible 网关 → 生产 Model Gateway。
