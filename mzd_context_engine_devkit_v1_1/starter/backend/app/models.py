from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Selection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=2000)
    startParagraphId: str
    endParagraphId: str
    startOffset: int | None = Field(default=None, ge=0)
    endOffset: int | None = Field(default=None, ge=0)


class InteractionEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    eventType: Literal[
        "anchor_changed",
        "paragraph_clicked",
        "text_selected",
        "entity_clicked",
        "question_submitted",
    ]
    releaseId: str
    articleId: str
    anchorId: str
    paragraphId: str | None = None
    selection: Selection | None = None
    entityId: str | None = None
    entityType: Literal["person", "organization", "place", "event", "concept"] | None = None
    mode: Literal["framework_stream"] = "framework_stream"
    question: str | None = Field(default=None, max_length=2000)
    currentUiHash: str | None = None
    uiVersion: int = Field(ge=1)
    occurredAt: datetime
    clientContext: dict[str, Any] | None = None


class CreateSessionRequest(BaseModel):
    releaseId: str
    articleId: str
    anchorId: str
    mode: Literal["framework_stream"] = "framework_stream"
    client: dict[str, Any] | None = None


class LLMSettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    baseUrl: str | None = Field(default=None, min_length=8, max_length=300)
    model: str | None = Field(default=None, min_length=1, max_length=120)
    apiKey: str | None = Field(default=None, min_length=1, max_length=4000)
    clearApiKey: bool = False
    temperature: float | None = Field(default=None, ge=0, le=2)
    imageBaseUrl: str | None = Field(default=None, min_length=8, max_length=300)
    imageModel: str | None = Field(default=None, min_length=1, max_length=120)
    imageSize: str | None = Field(default=None, min_length=4, max_length=40)
    imageQuality: Literal["low", "medium", "high", "auto"] | None = None
    imageOutputFormat: Literal["png", "webp", "jpeg"] | None = None


class LLMSettingsResponse(BaseModel):
    baseUrl: str
    model: str
    hasApiKey: bool
    apiKeySource: Literal["runtime", "environment", "missing"]
    temperature: float
    imageBaseUrl: str
    imageModel: str
    imageSize: str
    imageQuality: str
    imageOutputFormat: str


class WorkflowTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")
    targetType: Literal["article", "anchor", "paragraph", "selection", "person", "event", "place", "timeline", "illustration"]
    targetId: str | None = Field(default=None, max_length=200)
    label: str = Field(min_length=1, max_length=200)
    sourceIds: list[str] = Field(default_factory=list, max_length=20)


class WorkflowRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    releaseId: str
    articleId: str
    anchorId: str
    workflow: Literal[
        "article_overview",
        "timeline",
        "figure_network",
        "event_chain",
        "map_context",
        "illustration_prompt",
    ]
    target: WorkflowTarget
    mode: Literal["framework_stream"] = "framework_stream"
    uiVersion: int = Field(ge=1)
    occurredAt: datetime
    forceRegenerate: bool = False
