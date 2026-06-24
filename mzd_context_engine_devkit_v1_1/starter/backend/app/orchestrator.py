from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any, Literal

from .corpus import ArticleNotFound, corpus
from .llm import LLMConfigurationError, LLMProviderError, OpenAICompatibleStreamClient
from .models import InteractionEvent

Slot = Literal["writing_context", "era_context", "core_argument"]
SLOTS: list[Slot] = ["writing_context", "era_context", "core_argument"]
SLOT_TITLES: dict[Slot, str] = {
    "writing_context": "写作背景",
    "era_context": "时代背景",
    "core_argument": "核心论点",
}
SLOT_QUESTIONS: dict[Slot, str] = {
    "writing_context": "这篇文章写于什么时间地点？毛泽东当时在做什么工作、处于什么处境？",
    "era_context": "当时中国社会面临什么主要矛盾和问题？这篇文章回应了什么样的时代挑战？",
    "core_argument": "文章的核心主张是什么？毛泽东用什么推理逻辑得出结论？",
}
LABEL_RE = re.compile(r"^(标题|摘要|要点|来源)\s*[:：]\s*(.*)$")
SOURCE_RE = re.compile(r"\b(?:p|src)_[A-Za-z0-9_-]+\b")


class SlotParseError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sse(event_id: int, event: str, data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"id: {event_id}\nevent: {event}\ndata: {payload}\n\n"


def anchor_title(article: dict[str, Any], anchor_id: str) -> str:
    for anchor in article["anchors"]:
        if anchor["anchorId"] == anchor_id:
            return anchor["title"]
    return anchor_id


def anchor_paragraph_ids(article: dict[str, Any], anchor_id: str) -> list[str]:
    for anchor in article["anchors"]:
        if anchor["anchorId"] == anchor_id:
            return list(anchor["paragraphIds"])
    return []


def anchor_paragraphs(article: dict[str, Any], anchor_id: str) -> list[dict[str, Any]]:
    paragraph_ids = set(anchor_paragraph_ids(article, anchor_id))
    return [item for item in article["paragraphs"] if item["paragraphId"] in paragraph_ids]


def article_context(article: dict[str, Any], anchor_id: str) -> str:
    paragraphs = [
        f'{item["paragraphId"]}：{item["text"]}'
        for item in anchor_paragraphs(article, anchor_id)
    ]
    return "\n".join(paragraphs) or "当前锚点没有可用原文。"


def allowed_sources(article: dict[str, Any], anchor_id: str) -> set[str]:
    return {item["paragraphId"] for item in anchor_paragraphs(article, anchor_id)}


def paragraph_by_id(article: dict[str, Any], paragraph_id: str | None) -> dict[str, Any] | None:
    if not paragraph_id:
        return None
    return next((item for item in article["paragraphs"] if item["paragraphId"] == paragraph_id), None)


def user_focus(article: dict[str, Any], event: InteractionEvent) -> str:
    if event.eventType == "question_submitted" and event.question:
        return f"用户问题：{event.question}"
    if event.eventType == "text_selected" and event.selection:
        return f"用户选区：{event.selection.text}"
    paragraph = paragraph_by_id(article, event.paragraphId)
    if paragraph:
        return f'{event.paragraphId}：{paragraph["text"]}'
    return f"当前锚点：{event.anchorId}（{anchor_title(article, event.anchorId)}）"


def article_meta(article: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"文章：{article['title']}",
            f"版本：{article.get('canonicalEdition', '本地语料')}",
            f"卷册：{article.get('volumeTitle') or article.get('documentType') or '未标注'}",
            f"篇章位置：{article.get('sectionTitle') or article.get('location') or '未标注'}",
            f"时间：{article.get('dateDisplay') or '未标注'}",
            f"核心问题：{article['coreQuestion']}",
        ]
    )


def slot_messages(slot: Slot, event: InteractionEvent, article: dict[str, Any]) -> list[dict[str, str]]:
    sources = allowed_sources(article, event.anchorId)
    allowed = ", ".join(sorted(sources)) or "无"
    system = (
        "你是一个受控的大模型内容编排器，只能使用用户提供的当前原文片段。"
        "不要使用模型记忆补充具体事实，不要虚构历史背景，不要输出后见评价。"
        "如果当前原文不足以回答某个细节，必须说明资料不足。"
        "输出中文，必须严格使用指定格式，不要添加额外说明。"
    )
    user = f"""
产品固定槽位：{SLOT_TITLES[slot]}
槽位问题：{SLOT_QUESTIONS[slot]}

{article_meta(article)}
当前锚点：{event.anchorId}｜{anchor_title(article, event.anchorId)}
用户触发：{user_focus(article, event)}

当前锚点原文（唯一事实来源）：
{article_context(article, event.anchorId)}

允许引用的 sourceIds：
{allowed}

输出格式必须完全如下：
标题：不超过18个汉字
摘要：80到140个汉字，回答槽位问题
要点：
- 标签｜内容｜来源：sourceId1,sourceId2
- 标签｜内容｜来源：sourceId1

硬性要求：
1. sourceId 必须来自允许列表。
2. 最多 3 条要点。
3. 不确定就写资料不足，不要猜。
4. 不要输出 Markdown 表格、编号说明或 JSON。
""".strip()
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def parse_slot_card(
    slot: Slot,
    text: str,
    anchor_id: str,
    interaction_id: str,
    valid_sources: set[str],
) -> dict[str, Any]:
    headline = ""
    summary = ""
    points: list[dict[str, str]] = []
    in_points = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        label_match = LABEL_RE.match(line)
        if label_match:
            label, value = label_match.groups()
            if label == "标题":
                headline = value.strip()
            elif label == "摘要":
                summary = value.strip()
            elif label == "要点":
                in_points = True
            continue

        if in_points and line.startswith(("-", "•")):
            value = line.lstrip("-• ").strip()
            pieces = [piece.strip() for piece in re.split(r"[｜|]", value)]
            label = pieces[0] if pieces else "要点"
            content = pieces[1] if len(pieces) > 1 else value
            points.append({"label": label[:12], "text": content})

    sources = sorted(set(SOURCE_RE.findall(text)) & valid_sources)
    if not headline or not summary:
        raise SlotParseError(f"LLM output for {slot} did not include required title and summary labels")
    if not sources:
        raise SlotParseError(f"LLM output for {slot} did not include valid sourceIds")

    return {
        "slot": slot,
        "status": "ready",
        "headline": headline[:36],
        "summary": summary,
        "points": points[:3],
        "sourceIds": sources,
        "anchorIds": [anchor_id],
        "uncertainty": {"level": "none", "note": None},
        "generatedBy": {
            "kind": "real_llm_stream",
            "promptVersion": f"{slot}_framework_stream@2.1.0",
            "runId": f"run_{interaction_id.removeprefix('int_')}_{slot}",
        },
    }


async def stream_slot(
    event_id: int,
    interaction_id: str,
    event: InteractionEvent,
    article: dict[str, Any],
    slot: Slot,
    client: OpenAICompatibleStreamClient,
) -> AsyncIterator[tuple[int, str]]:
    common = {"interactionId": interaction_id, "uiVersion": event.uiVersion}
    yield event_id, sse(event_id, "slot.started", {**common, "timestamp": utc_now(), "slot": slot})
    event_id += 1

    accumulated = ""
    last_sent_len = 0
    async for chunk in client.stream_chat(slot_messages(slot, event, article)):
        accumulated += chunk
        if len(accumulated) - last_sent_len >= 80 or "\n" in accumulated[last_sent_len:]:
            yield event_id, sse(
                event_id,
                "slot.block",
                {
                    **common,
                    "timestamp": utc_now(),
                    "slot": slot,
                    "kind": "draft",
                    "index": event_id,
                    "text": accumulated.strip(),
                },
            )
            event_id += 1
            last_sent_len = len(accumulated)

    card = parse_slot_card(slot, accumulated, event.anchorId, interaction_id, allowed_sources(article, event.anchorId))
    yield event_id, sse(event_id, "slot.committed", {**common, "timestamp": utc_now(), "slot": slot, "payload": card})


async def llm_stream(interaction_id: str, event: InteractionEvent) -> AsyncIterator[str]:
    common = {"interactionId": interaction_id, "uiVersion": event.uiVersion}
    event_id = 1
    yield sse(event_id, "interaction.accepted", {**common, "timestamp": utc_now(), "status": "accepted"})
    event_id += 1
    yield sse(
        event_id,
        "plan.committed",
        {
            **common,
            "timestamp": utc_now(),
            "framework": "fixed_three_slot_context_reader",
            "updateSlots": SLOTS,
            "keepSlots": [],
            "timePolicy": "framework_stream_only",
        },
    )
    event_id += 1

    try:
        article = corpus.get_article(event.articleId, event.releaseId)
        if not allowed_sources(article, event.anchorId):
            raise ArticleNotFound("anchor not found")

        client = OpenAICompatibleStreamClient()
        for slot in SLOTS:
            async for next_event_id, chunk in stream_slot(event_id, interaction_id, event, article, slot, client):
                event_id = next_event_id + 1
                yield chunk

        yield sse(
            event_id,
            "interaction.completed",
            {
                **common,
                "timestamp": utc_now(),
                "status": "completed",
                "updatedSlots": SLOTS,
                "resultUrl": f"/api/v1/interactions/{interaction_id}",
            },
        )
    except (ArticleNotFound, LLMConfigurationError, LLMProviderError, SlotParseError) as exc:
        yield sse(
            event_id,
            "interaction.failed",
            {
                **common,
                "timestamp": utc_now(),
                "error": {
                    "code": exc.__class__.__name__.upper(),
                    "message": str(exc),
                    "retryable": isinstance(exc, LLMProviderError),
                },
            },
        )
