from __future__ import annotations

import base64
import binascii
import hashlib
import json
import math
import os
import re
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .corpus import ArticleNotFound, corpus
from .llm import (
    ImageGenerationError,
    LLMConfigurationError,
    LLMProviderError,
    OpenAICompatibleImageClient,
    OpenAICompatibleStreamClient,
)
from .models import WorkflowRequest
from .orchestrator import anchor_paragraphs

WorkflowArtifactCallback = Callable[[dict[str, Any]], None]

GENERATED_ROOT = Path(os.getenv("GENERATED_DIR", Path(__file__).resolve().parents[2] / "generated"))
ILLUSTRATION_DIR = GENERATED_ROOT / "illustrations"

WORKFLOW_TITLES = {
    "article_overview": "全篇总览",
    "timeline": "进度时间线",
    "figure_network": "关键人物关系",
    "event_chain": "关键事件链",
    "map_context": "地图语境",
    "illustration_prompt": "插图生成提示",
}

WORKFLOW_SUBAGENTS = {
    "article_overview": ["article_scanner", "context_mapper", "reasoning_synthesizer"],
    "timeline": ["temporal_extractor", "sequence_checker"],
    "figure_network": ["figure_extractor", "relation_mapper"],
    "event_chain": ["event_extractor", "causal_chain_checker"],
    "map_context": ["place_extractor", "spatial_context_mapper"],
    "illustration_prompt": ["scene_selector", "image_prompt_writer"],
}

WORKFLOW_INSTRUCTIONS = {
    "article_overview": "生成全篇整体阅读导览：核心问题、结构推进、可点击的后续探索方向。",
    "timeline": "从当前原文中提取时间、阶段、先后关系；没有明确时间时说明资料不足。",
    "figure_network": "只从当前原文识别人物、组织和关系；不要凭记忆补充人物。",
    "event_chain": "提取关键事件、触发、约束和文本中的判断链；只使用给定原文。",
    "map_context": "识别地点、区域、阶层、路线或空间关系；把可视化所需变量单独写入“地图变量”。若原文未标明真实地点，输出文本支持的语义空间变量，不伪造地名。",
    "illustration_prompt": "为图像模型生成可审核插图提示词，只描绘文本可支持的场景，不塑造未经支持的人物外貌。",
}


class AgentWorkflowError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sse(event_id: int, event: str, data: dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"id: {event_id}\nevent: {event}\ndata: {payload}\n\n"


def normalize_image_extension(output_format: str) -> str:
    output_format = output_format.lower().strip(".")
    if output_format == "jpeg":
        return "jpg"
    return output_format if output_format in {"png", "webp", "jpg"} else "png"


def image_url_for_saved_file(path: Path) -> str:
    return f"/generated/illustrations/{path.name}"


def save_image_result(workflow_id: str, result: dict[str, Any], prompt: str) -> dict[str, Any]:
    if result.get("kind") == "url":
        return {
            "imageUrl": result["url"],
            "prompt": prompt,
            "model": result.get("model"),
            "outputFormat": result.get("outputFormat"),
            "storage": "provider_url",
            "usage": result.get("usage"),
        }

    ext = normalize_image_extension(str(result.get("outputFormat") or "png"))
    ILLUSTRATION_DIR.mkdir(parents=True, exist_ok=True)
    path = ILLUSTRATION_DIR / f"{workflow_id}.{ext}"
    try:
        image_bytes = base64.b64decode(result["b64_json"], validate=True)
    except (KeyError, binascii.Error, ValueError) as exc:
        raise ImageGenerationError("Image provider returned invalid base64 image data") from exc
    path.write_bytes(image_bytes)
    return {
        "imageUrl": image_url_for_saved_file(path),
        "prompt": prompt,
        "model": result.get("model"),
        "outputFormat": result.get("outputFormat") or ext,
        "storage": "local_generated_asset",
        "usage": result.get("usage"),
    }


def extract_illustration_prompt(artifact_text: str) -> str:
    match = re.search(r"插图提示[:：]\s*(.+)", artifact_text, flags=re.S)
    prompt = match.group(1).strip() if match else artifact_text.strip()
    prompt = prompt.strip("` \n\r\t-")
    if not prompt or prompt in {"无", "无。", "无；"}:
        raise AgentWorkflowError("LLM did not return a usable illustration prompt")
    return prompt


def build_image_prompt(article: dict[str, Any], req: WorkflowRequest, artifact_text: str) -> str:
    prompt = extract_illustration_prompt(artifact_text)
    return f"""
为历史阅读软件生成一张可审核的文章插图。画面必须只依据给定文本提示，不补充未经支持的具体人物肖像或夸张宣传元素。

文章：{article["title"]}
版本：{article.get("canonicalEdition", "本地语料")}
当前锚点：{req.anchorId}
插图提示：{prompt}

视觉要求：Apple 风格软件中的严肃编辑插图，克制、清晰、文献感；可用于阅读界面侧栏预览；避免海报标语、水印、现代 UI 文字、真实领袖肖像特写。
""".strip()


def stable_semantic_point(seed: str, index: int) -> tuple[float, float]:
    digest = hashlib.sha1(seed.encode("utf-8")).digest()
    angle_seed = int.from_bytes(digest[:2], "big") / 65535
    radius_seed = int.from_bytes(digest[2:4], "big") / 65535
    angle = (angle_seed * math.tau) + index * 0.72
    radius = 2.4 + radius_seed * 5.8
    return 35.8 + radius * 0.68 * math.sin(angle), 104.2 + radius * math.cos(angle)


def article_source_ids(article: dict[str, Any]) -> set[str]:
    return {item["paragraphId"] for item in article.get("paragraphs", [])}


def extract_source_ids(raw: str, article: dict[str, Any], req: WorkflowRequest) -> list[str]:
    allowed = article_source_ids(article)
    candidates = [item.strip(" ，,;；") for item in re.split(r"[\s,，、;；]+", raw) if item.strip(" ，,;；")]
    source_ids = [item for item in candidates if item in allowed]
    if source_ids:
        return source_ids[:8]
    if req.target.sourceIds:
        return [item for item in req.target.sourceIds if item in allowed][:8]
    return [item["paragraphId"] for item in anchor_paragraphs(article, req.anchorId)[:3]]


def parse_map_variable_lines(section: str, article: dict[str, Any], req: WorkflowRequest) -> list[dict[str, Any]]:
    variables: list[dict[str, Any]] = []
    for line in section.splitlines():
        item = line.strip().lstrip("-*• ").strip()
        if not item or item in {"无", "无。"}:
            continue
        source_match = re.search(r"来源[:：]\s*(.+)$", item)
        source_ids = extract_source_ids(source_match.group(1), article, req) if source_match else extract_source_ids("", article, req)
        clean = re.sub(r"来源[:：].+$", "", item).strip(" |｜")
        parts = [part.strip() for part in re.split(r"[|｜]", clean) if part.strip()]
        if len(parts) < 2:
            continue
        kind = parts[0][:16]
        label = parts[1][:30]
        description = parts[2][:120] if len(parts) >= 3 else label
        lat, lng = stable_semantic_point(f"{req.articleId}:{label}:{','.join(source_ids)}", len(variables))
        variables.append(
            {
                "id": f"ai_map_{hashlib.sha1((label + ''.join(source_ids)).encode('utf-8')).hexdigest()[:10]}",
                "label": label,
                "description": description,
                "sourceIds": source_ids,
                "lat": round(lat, 5),
                "lng": round(lng, 5),
                "weight": max(1, len(source_ids)),
                "kind": "semantic" if kind not in {"地点", "区域", "路线"} else kind,
            }
        )
        if len(variables) >= 12:
            break
    return variables


def fallback_map_variables(article: dict[str, Any], req: WorkflowRequest) -> list[dict[str, Any]]:
    variables: list[dict[str, Any]] = []
    for index, anchor in enumerate(article.get("anchors", [])[:8]):
        label = re.sub(r"^第\d+组[:：]\s*", "", anchor["title"])[:30]
        lat, lng = stable_semantic_point(f"{req.articleId}:{anchor['anchorId']}", index)
        variables.append(
            {
                "id": f"ai_map_{anchor['anchorId']}",
                "label": label,
                "description": "由文章锚点生成的语义阅读位置",
                "sourceIds": anchor.get("paragraphIds", [])[:8],
                "lat": round(lat, 5),
                "lng": round(lng, 5),
                "weight": max(1, len(anchor.get("paragraphIds", []))),
                "kind": "semantic",
            }
        )
    return variables


def extract_map_variables(article: dict[str, Any], req: WorkflowRequest, artifact_text: str) -> list[dict[str, Any]]:
    map_match = re.search(r"地图变量[:：]\s*(.*?)(?:\n(?:建议点击|插图提示)[:：]|\Z)", artifact_text, flags=re.S)
    if map_match:
        variables = parse_map_variable_lines(map_match.group(1), article, req)
        if variables:
            return variables
    finding_match = re.search(r"发现[:：]\s*(.*?)(?:\n(?:地图变量|建议点击|插图提示)[:：]|\Z)", artifact_text, flags=re.S)
    if finding_match:
        variables = parse_map_variable_lines(finding_match.group(1), article, req)
        if variables:
            return variables
    return fallback_map_variables(article, req)


async def cached_agent_stream(workflow_id: str, req: WorkflowRequest, cached: dict[str, Any]) -> AsyncIterator[str]:
    event_id = 1
    common = {"workflowId": workflow_id, "uiVersion": req.uiVersion, "workflow": req.workflow}
    yield sse(
        event_id,
        "workflow.accepted",
        {**common, "timestamp": utc_now(), "title": WORKFLOW_TITLES[req.workflow], "cached": True},
    )
    event_id += 1

    artifact = dict(cached["artifact"])
    artifact.update(common)
    artifact.update({"timestamp": utc_now(), "cached": True})
    yield sse(event_id, "artifact.committed", artifact)
    event_id += 1

    image = cached.get("image")
    if image:
        image_event = dict(image)
        image_event.update(common)
        image_event.update({"timestamp": utc_now(), "cached": True})
        yield sse(event_id, "image.committed", image_event)
        event_id += 1

    map_variables = cached.get("mapVariables")
    if map_variables:
        map_event = dict(map_variables)
        map_event.update(common)
        map_event.update({"timestamp": utc_now(), "cached": True})
        yield sse(event_id, "map.variables.committed", map_event)
        event_id += 1

    yield sse(event_id, "workflow.completed", {**common, "timestamp": utc_now(), "status": "completed", "cached": True})


def compact_article_context(article: dict[str, Any], req: WorkflowRequest) -> str:
    if req.target.targetType == "article":
        paragraphs = article["paragraphs"][:12]
    else:
        paragraphs = anchor_paragraphs(article, req.anchorId)
    if req.target.sourceIds:
        selected = [item for item in article["paragraphs"] if item["paragraphId"] in set(req.target.sourceIds)]
        if selected:
            paragraphs = selected
    lines = [f'{item["paragraphId"]}：{item["text"]}' for item in paragraphs[:16]]
    return "\n".join(lines) or "没有可用原文。"


def source_allowlist(article: dict[str, Any], req: WorkflowRequest) -> str:
    if req.target.sourceIds:
        return ", ".join(req.target.sourceIds)
    if req.target.targetType == "article":
        return ", ".join(item["paragraphId"] for item in article["paragraphs"][:12])
    return ", ".join(item["paragraphId"] for item in anchor_paragraphs(article, req.anchorId))


def workflow_messages(article: dict[str, Any], req: WorkflowRequest) -> list[dict[str, str]]:
    title = WORKFLOW_TITLES[req.workflow]
    instruction = WORKFLOW_INSTRUCTIONS[req.workflow]
    map_output = (
        "地图变量：\n- 类型｜名称｜说明｜来源：sourceId1,sourceId2\n"
        if req.workflow == "map_context"
        else ""
    )
    system = (
        "你是历史阅读智能系统中的 agent 编排器。"
        "你只能使用给定原文，不得调用模型记忆补充具体事实。"
        "需要把输出组织成可点击 UI 所需的结构化中文文本。"
        "不确定时明确写资料不足。"
    )
    user = f"""
工作流：{title}
任务：{instruction}

文章：{article["title"]}
版本：{article.get("canonicalEdition", "本地语料")}
卷册：{article.get("volumeTitle") or article.get("documentType") or "未标注"}
时间：{article.get("dateDisplay") or "未标注"}
当前锚点：{req.anchorId}
点击目标：{req.target.targetType}｜{req.target.label}｜{req.target.targetId or "no-id"}

原文：
{compact_article_context(article, req)}

允许引用 sourceIds：
{source_allowlist(article, req)}

输出格式：
标题：不超过18字
摘要：80到160字
发现：
- 类型｜名称｜说明｜来源：sourceId1,sourceId2
{map_output}建议点击：
- 动作｜标签｜原因
插图提示：如果工作流不是插图，写“无”；如果是插图，写一段给图像模型的中文提示词。

硬性要求：
1. 每条发现的来源必须来自允许引用 sourceIds。
2. 不输出 Markdown 表格，不输出 JSON。
3. 不得把后世结果写成当时已知事实。
""".strip()
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


async def agent_stream(
    workflow_id: str,
    req: WorkflowRequest,
    on_artifact: WorkflowArtifactCallback | None = None,
) -> AsyncIterator[str]:
    event_id = 1
    common = {"workflowId": workflow_id, "uiVersion": req.uiVersion, "workflow": req.workflow}
    yield sse(event_id, "workflow.accepted", {**common, "timestamp": utc_now(), "title": WORKFLOW_TITLES[req.workflow]})
    event_id += 1

    try:
        article = corpus.get_article(req.articleId, req.releaseId)
        if not any(anchor["anchorId"] == req.anchorId for anchor in article["anchors"]):
            raise ArticleNotFound("anchor not found")

        subagents = WORKFLOW_SUBAGENTS[req.workflow]
        for index, subagent in enumerate(subagents, start=1):
            yield sse(
                event_id,
                "subagent.started",
                {**common, "timestamp": utc_now(), "subagent": subagent, "index": index, "total": len(subagents)},
            )
            event_id += 1

        client = OpenAICompatibleStreamClient()
        accumulated = ""
        last_sent_len = 0
        async for chunk in client.stream_chat(workflow_messages(article, req)):
            accumulated += chunk
            if len(accumulated) - last_sent_len >= 90 or "\n" in accumulated[last_sent_len:]:
                yield sse(
                    event_id,
                    "artifact.block",
                    {
                        **common,
                        "timestamp": utc_now(),
                        "target": req.target.model_dump(),
                        "text": accumulated.strip(),
                    },
                )
                event_id += 1
                last_sent_len = len(accumulated)

        if not accumulated.strip():
            raise AgentWorkflowError("LLM returned an empty workflow artifact")

        artifact_payload = {
            **common,
            "timestamp": utc_now(),
            "target": req.target.model_dump(),
            "title": WORKFLOW_TITLES[req.workflow],
            "text": accumulated.strip(),
            "generatedBy": {
                "kind": "real_llm_agent",
                "subagents": subagents,
                "runId": f"run_{workflow_id.removeprefix('wf_')}",
            },
        }
        yield sse(event_id, "artifact.committed", artifact_payload)
        event_id += 1

        map_payload = None
        if req.workflow == "map_context":
            map_payload = {
                **common,
                "timestamp": utc_now(),
                "target": req.target.model_dump(),
                "variables": extract_map_variables(article, req, accumulated.strip()),
                "generatedBy": {
                    "kind": "real_llm_map_variables",
                    "subagents": subagents,
                    "runId": f"run_{workflow_id.removeprefix('wf_')}",
                },
            }
            yield sse(event_id, "map.variables.committed", map_payload)
            event_id += 1

        image_payload = None
        if req.workflow == "illustration_prompt":
            image_prompt = build_image_prompt(article, req, accumulated.strip())
            yield sse(
                event_id,
                "image.started",
                {**common, "timestamp": utc_now(), "target": req.target.model_dump(), "prompt": image_prompt},
            )
            event_id += 1
            try:
                image_result = await OpenAICompatibleImageClient().generate_image(image_prompt)
                image_payload = {
                    **common,
                    "timestamp": utc_now(),
                    "target": req.target.model_dump(),
                    **save_image_result(workflow_id, image_result, image_prompt),
                }
                yield sse(event_id, "image.committed", image_payload)
                event_id += 1
            except (LLMConfigurationError, ImageGenerationError) as exc:
                yield sse(
                    event_id,
                    "image.failed",
                    {
                        **common,
                        "timestamp": utc_now(),
                        "error": {
                            "code": exc.__class__.__name__.upper(),
                            "message": str(exc),
                            "retryable": isinstance(exc, ImageGenerationError),
                        },
                    },
                )
                event_id += 1
                raise

        if on_artifact:
            on_artifact(
                {
                    "artifact": artifact_payload,
                    "image": image_payload,
                    "mapVariables": map_payload,
                    "cachedAt": utc_now(),
                }
            )

        yield sse(event_id, "workflow.completed", {**common, "timestamp": utc_now(), "status": "completed"})
    except (ArticleNotFound, LLMConfigurationError, LLMProviderError, ImageGenerationError, AgentWorkflowError) as exc:
        yield sse(
            event_id,
            "workflow.failed",
            {
                **common,
                "timestamp": utc_now(),
                "error": {
                    "code": exc.__class__.__name__.upper(),
                    "message": str(exc),
                    "retryable": isinstance(exc, (LLMProviderError, ImageGenerationError)),
                },
            },
        )
