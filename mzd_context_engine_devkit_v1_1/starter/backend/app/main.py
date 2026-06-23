from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .agents import agent_stream, cached_agent_stream
from .corpus import ArticleNotFound, corpus
from .llm import runtime_llm_settings
from .models import CreateSessionRequest, InteractionEvent, LLMSettingsResponse, LLMSettingsUpdate, WorkflowRequest
from .orchestrator import llm_stream
from .store import workflow_artifact_store

app = FastAPI(title="Historical Context Engine Starter", version="1.1.0")

SESSIONS: dict[str, dict[str, Any]] = {}
INTERACTIONS: dict[str, dict[str, Any]] = {}
WORKFLOWS: dict[str, dict[str, Any]] = {}
WORKFLOW_ARTIFACTS: dict[str, dict[str, Any]] = workflow_artifact_store.load_all()
IDEMPOTENCY: dict[tuple[str, str], str] = {}

WEB_DIR = Path(os.getenv("WEB_DIR", Path(__file__).resolve().parents[2] / "web"))
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

GENERATED_DIR = Path(os.getenv("GENERATED_DIR", Path(__file__).resolve().parents[2] / "generated"))
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/generated", StaticFiles(directory=GENERATED_DIR), name="generated")


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def workflow_cache_key(req: WorkflowRequest) -> str:
    return json.dumps(
        {
            "releaseId": req.releaseId,
            "articleId": req.articleId,
            "anchorId": req.anchorId,
            "workflow": req.workflow,
            "target": req.target.model_dump(mode="json"),
            "mode": req.mode,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


@app.get("/")
def index() -> FileResponse:
    path = WEB_DIR / "index.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="web prototype not found")
    return FileResponse(path)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/articles")
def list_articles(limit: int = Query(default=500, ge=1, le=500)) -> dict[str, Any]:
    items = corpus.list_articles()
    return {"items": items[:limit], "total": len(items), "source": "local_jinghuo_markdown"}


@app.get("/api/v1/articles/{article_id}")
def get_article(article_id: str, releaseId: str) -> dict[str, Any]:
    try:
        return corpus.get_article(article_id, releaseId)
    except ArticleNotFound as exc:
        raise HTTPException(status_code=404, detail="article/release not found") from exc


@app.get("/api/v1/settings/llm", response_model=LLMSettingsResponse)
def get_llm_settings() -> dict[str, Any]:
    return runtime_llm_settings.summary()


@app.put("/api/v1/settings/llm", response_model=LLMSettingsResponse)
def update_llm_settings(req: LLMSettingsUpdate) -> dict[str, Any]:
    return runtime_llm_settings.update(
        api_key=req.apiKey,
        clear_api_key=req.clearApiKey,
        model=req.model,
        base_url=req.baseUrl,
        temperature=req.temperature,
        image_model=req.imageModel,
        image_base_url=req.imageBaseUrl,
        image_size=req.imageSize,
        image_quality=req.imageQuality,
        image_output_format=req.imageOutputFormat,
    )


@app.post("/api/v1/reading-sessions", status_code=201)
def create_session(req: CreateSessionRequest) -> dict[str, Any]:
    try:
        article = corpus.get_article(req.articleId, req.releaseId)
    except ArticleNotFound as exc:
        raise HTTPException(status_code=404, detail="article/release not found") from exc
    if not any(anchor["anchorId"] == req.anchorId for anchor in article["anchors"]):
        raise HTTPException(status_code=404, detail="anchor not found")

    session_id = f"ses_{uuid.uuid4().hex[:12]}"
    session = {
        "sessionId": session_id,
        "releaseId": req.releaseId,
        "articleId": req.articleId,
        "anchorId": req.anchorId,
        "mode": req.mode,
        "createdAt": now(),
    }
    SESSIONS[session_id] = session
    return session


@app.post("/api/v1/reading-sessions/{session_id}/interactions", status_code=202)
def create_interaction(
    session_id: str,
    event: InteractionEvent,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    if event.articleId != session["articleId"] or event.releaseId != session["releaseId"]:
        raise HTTPException(status_code=409, detail="interaction article does not match session")
    if not corpus.has_anchor(event.articleId, event.releaseId, event.anchorId):
        raise HTTPException(status_code=404, detail="anchor not found")

    key = idempotency_key or uuid.uuid4().hex
    existing = IDEMPOTENCY.get((session_id, key))
    if existing:
        record = INTERACTIONS[existing]
        return record["accepted"]

    interaction_id = f"int_{uuid.uuid4().hex[:12]}"
    accepted = {
        "interactionId": interaction_id,
        "status": "accepted",
        "streamUrl": f"/api/v1/interactions/{interaction_id}/events",
        "pollUrl": f"/api/v1/interactions/{interaction_id}",
        "uiVersion": event.uiVersion,
    }
    INTERACTIONS[interaction_id] = {"event": event, "accepted": accepted, "status": "accepted"}
    IDEMPOTENCY[(session_id, key)] = interaction_id
    return accepted


@app.post("/api/v1/reading-sessions/{session_id}/workflows", status_code=202)
def create_workflow(
    session_id: str,
    req: WorkflowRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    if req.articleId != session["articleId"] or req.releaseId != session["releaseId"]:
        raise HTTPException(status_code=409, detail="workflow article does not match session")
    if not corpus.has_anchor(req.articleId, req.releaseId, req.anchorId):
        raise HTTPException(status_code=404, detail="anchor not found")

    key = idempotency_key or uuid.uuid4().hex
    existing = IDEMPOTENCY.get((session_id, f"workflow:{key}"))
    if existing:
        return WORKFLOWS[existing]["accepted"]

    cache_key = workflow_cache_key(req)
    cached_artifact = None
    if not req.forceRegenerate:
        cached_artifact = WORKFLOW_ARTIFACTS.get(cache_key) or workflow_artifact_store.get(cache_key)
        if cached_artifact:
            WORKFLOW_ARTIFACTS[cache_key] = cached_artifact
    workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
    accepted = {
        "workflowId": workflow_id,
        "status": "accepted",
        "streamUrl": f"/api/v1/workflows/{workflow_id}/events",
        "pollUrl": f"/api/v1/workflows/{workflow_id}",
        "uiVersion": req.uiVersion,
        "cached": bool(cached_artifact),
    }
    WORKFLOWS[workflow_id] = {
        "request": req,
        "accepted": accepted,
        "status": "accepted",
        "cacheKey": cache_key,
        "cachedArtifact": cached_artifact,
    }
    IDEMPOTENCY[(session_id, f"workflow:{key}")] = workflow_id
    return accepted


@app.get("/api/v1/interactions/{interaction_id}/events")
def interaction_events(interaction_id: str) -> StreamingResponse:
    record = INTERACTIONS.get(interaction_id)
    if not record:
        raise HTTPException(status_code=404, detail="interaction not found")
    record["status"] = "running"

    async def stream():
        async for chunk in llm_stream(interaction_id, record["event"]):
            if "\nevent: interaction.failed\n" in chunk:
                record["status"] = "failed"
            yield chunk
        if record["status"] == "running":
            record["status"] = "completed"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )


@app.get("/api/v1/workflows/{workflow_id}/events")
def workflow_events(workflow_id: str) -> StreamingResponse:
    record = WORKFLOWS.get(workflow_id)
    if not record:
        raise HTTPException(status_code=404, detail="workflow not found")
    record["status"] = "running"

    async def stream():
        cached = record.get("cachedArtifact")
        if cached:
            async for chunk in cached_agent_stream(workflow_id, record["request"], cached):
                yield chunk
            record["status"] = "completed"
            return

        def store_artifact(artifact: dict[str, Any]) -> None:
            WORKFLOW_ARTIFACTS[record["cacheKey"]] = artifact
            workflow_artifact_store.put(record["cacheKey"], artifact)
            record["artifact"] = artifact

        async for chunk in agent_stream(workflow_id, record["request"], on_artifact=store_artifact):
            if "\nevent: workflow.failed\n" in chunk:
                record["status"] = "failed"
            yield chunk
        if record["status"] == "running":
            record["status"] = "completed"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )


@app.get("/api/v1/interactions/{interaction_id}")
def get_interaction(interaction_id: str) -> dict[str, Any]:
    record = INTERACTIONS.get(interaction_id)
    if not record:
        raise HTTPException(status_code=404, detail="interaction not found")
    return {
        "interactionId": interaction_id,
        "status": record["status"],
        "uiVersion": record["event"].uiVersion,
    }


@app.get("/api/v1/workflows/{workflow_id}")
def get_workflow(workflow_id: str) -> dict[str, Any]:
    record = WORKFLOWS.get(workflow_id)
    if not record:
        raise HTTPException(status_code=404, detail="workflow not found")
    return {
        "workflowId": workflow_id,
        "status": record["status"],
        "workflow": record["request"].workflow,
        "uiVersion": record["request"].uiVersion,
        "cached": bool(record.get("cachedArtifact")),
        "hasArtifact": bool(record.get("artifact") or record.get("cachedArtifact")),
    }


@app.post("/api/v1/interactions/{interaction_id}/cancel", status_code=202)
def cancel_interaction(interaction_id: str) -> dict[str, Any]:
    record = INTERACTIONS.get(interaction_id)
    if not record:
        raise HTTPException(status_code=404, detail="interaction not found")
    record["status"] = "cancelled"
    return {"interactionId": interaction_id, "status": "cancelled"}
