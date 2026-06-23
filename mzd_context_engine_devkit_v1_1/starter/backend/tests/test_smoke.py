from fastapi.testclient import TestClient

from app.main import WORKFLOW_ARTIFACTS, app, workflow_cache_key
from app.models import WorkflowRequest
from app.store import WorkflowArtifactStore, workflow_artifact_store

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_article_and_interaction_stream_requires_real_llm(monkeypatch) -> None:
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    response = client.get("/api/v1/articles")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) >= 200
    assert items[0]["articleId"] == "art_mzd_001"
    assert items[0]["title"] == "中国社会各阶级的分析"

    article_id = items[0]["articleId"]
    release_id = items[0]["currentReleaseId"]
    response = client.get(f"/api/v1/articles/{article_id}", params={"releaseId": release_id})
    assert response.status_code == 200
    article = response.json()
    assert article["articleId"] == article_id
    assert article["paragraphs"][0]["text"].startswith("毛泽东此文")
    anchor_id = article["anchors"][0]["anchorId"]

    response = client.post(
        "/api/v1/reading-sessions",
        json={
            "releaseId": release_id,
            "articleId": article_id,
            "anchorId": anchor_id,
            "mode": "framework_stream",
        },
    )
    assert response.status_code == 201
    session_id = response.json()["sessionId"]

    response = client.post(
        f"/api/v1/reading-sessions/{session_id}/interactions",
        headers={"Idempotency-Key": "test-framework-stream"},
        json={
            "eventType": "anchor_changed",
            "releaseId": release_id,
            "articleId": article_id,
            "anchorId": anchor_id,
            "mode": "framework_stream",
            "uiVersion": 1,
            "occurredAt": "2026-06-22T00:00:00Z",
        },
    )
    assert response.status_code == 202
    stream_url = response.json()["streamUrl"]

    with client.stream("GET", stream_url) as stream_response:
        body = "".join(stream_response.iter_text())

    assert "event: plan.committed" in body
    assert "fixed_three_slot_context_reader" in body
    assert "event: interaction.failed" in body
    assert "Missing required LLM setting" in body


def test_llm_settings_can_be_added_without_echoing_secret(monkeypatch) -> None:
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    response = client.get("/api/v1/settings/llm")
    assert response.status_code == 200
    assert "apiKey" not in response.json()

    response = client.put(
        "/api/v1/settings/llm",
        json={
            "baseUrl": "https://api.example.com/v1",
            "model": "unit-test-model",
            "apiKey": "sk-test-secret",
            "temperature": 0.4,
            "imageBaseUrl": "https://api.example.com/v1",
            "imageModel": "gpt-image-2",
            "imageSize": "1536x1024",
            "imageQuality": "medium",
            "imageOutputFormat": "webp",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["baseUrl"] == "https://api.example.com/v1"
    assert payload["model"] == "unit-test-model"
    assert payload["hasApiKey"] is True
    assert payload["apiKeySource"] == "runtime"
    assert payload["temperature"] == 0.4
    assert payload["imageBaseUrl"] == "https://api.example.com/v1"
    assert payload["imageModel"] == "gpt-image-2"
    assert payload["imageSize"] == "1536x1024"
    assert payload["imageQuality"] == "medium"
    assert payload["imageOutputFormat"] == "webp"
    assert "sk-test-secret" not in response.text


def test_workflow_artifact_store_roundtrip(tmp_path) -> None:
    db_path = tmp_path / "workflow_artifacts.sqlite3"
    store = WorkflowArtifactStore(db_path)
    artifact = {
        "artifact": {"title": "全篇总览", "text": "持久化结果"},
        "image": None,
        "cachedAt": "2026-06-23T00:00:00Z",
    }

    store.put("cache-key-1", artifact)
    assert store.get("cache-key-1") == artifact

    reloaded = WorkflowArtifactStore(db_path)
    assert reloaded.load_all()["cache-key-1"]["artifact"]["text"] == "持久化结果"


def test_agent_workflow_stream_requires_real_llm(monkeypatch) -> None:
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    WORKFLOW_ARTIFACTS.clear()
    workflow_artifact_store.clear()

    settings_response = client.put(
        "/api/v1/settings/llm",
        json={
            "baseUrl": "https://api.example.com/v1",
            "model": "unit-test-model",
            "clearApiKey": True,
        },
    )
    assert settings_response.status_code == 200

    articles = client.get("/api/v1/articles").json()["items"]
    article_id = articles[0]["articleId"]
    release_id = articles[0]["currentReleaseId"]
    article = client.get(f"/api/v1/articles/{article_id}", params={"releaseId": release_id}).json()
    anchor_id = article["anchors"][0]["anchorId"]

    session_response = client.post(
        "/api/v1/reading-sessions",
        json={
            "releaseId": release_id,
            "articleId": article_id,
            "anchorId": anchor_id,
            "mode": "framework_stream",
        },
    )
    assert session_response.status_code == 201
    session_id = session_response.json()["sessionId"]

    workflow_response = client.post(
        f"/api/v1/reading-sessions/{session_id}/workflows",
        headers={"Idempotency-Key": "test-agent-workflow"},
        json={
            "releaseId": release_id,
            "articleId": article_id,
            "anchorId": anchor_id,
            "workflow": "figure_network",
            "target": {
                "targetType": "person",
                "targetId": anchor_id,
                "label": "关键人物",
                "sourceIds": article["anchors"][0]["paragraphIds"],
            },
            "mode": "framework_stream",
            "uiVersion": 3,
            "occurredAt": "2026-06-22T00:00:00Z",
            "forceRegenerate": True,
        },
    )
    assert workflow_response.status_code == 202

    with client.stream("GET", workflow_response.json()["streamUrl"]) as stream_response:
        body = "".join(stream_response.iter_text())

    assert "event: workflow.accepted" in body
    assert "event: subagent.started" in body
    assert "event: workflow.failed" in body
    assert "Missing required LLM setting" in body


def test_agent_workflow_can_replay_cached_real_artifact(monkeypatch) -> None:
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    WORKFLOW_ARTIFACTS.clear()
    workflow_artifact_store.clear()

    articles = client.get("/api/v1/articles").json()["items"]
    article_id = articles[0]["articleId"]
    release_id = articles[0]["currentReleaseId"]
    article = client.get(f"/api/v1/articles/{article_id}", params={"releaseId": release_id}).json()
    anchor_id = article["anchors"][0]["anchorId"]

    session_response = client.post(
        "/api/v1/reading-sessions",
        json={
            "releaseId": release_id,
            "articleId": article_id,
            "anchorId": anchor_id,
            "mode": "framework_stream",
        },
    )
    session_id = session_response.json()["sessionId"]
    payload = {
        "releaseId": release_id,
        "articleId": article_id,
        "anchorId": anchor_id,
        "workflow": "article_overview",
        "target": {
            "targetType": "article",
            "targetId": article_id,
            "label": "全篇总览",
            "sourceIds": article["anchors"][0]["paragraphIds"],
        },
        "mode": "framework_stream",
        "uiVersion": 5,
        "occurredAt": "2026-06-22T00:00:00Z",
    }
    cache_key = workflow_cache_key(WorkflowRequest.model_validate(payload))
    WORKFLOW_ARTIFACTS[cache_key] = {
        "artifact": {
            "target": payload["target"],
            "title": "全篇总览",
            "text": "这是一条已经由真实模型生成并保存的运行结果。",
            "generatedBy": {"kind": "real_llm_agent", "runId": "run_cached"},
        },
        "image": None,
        "cachedAt": "2026-06-22T00:00:00Z",
    }

    workflow_response = client.post(
        f"/api/v1/reading-sessions/{session_id}/workflows",
        headers={"Idempotency-Key": "test-cached-workflow"},
        json=payload,
    )
    assert workflow_response.status_code == 202
    assert workflow_response.json()["cached"] is True

    with client.stream("GET", workflow_response.json()["streamUrl"]) as stream_response:
        body = "".join(stream_response.iter_text())

    assert "event: artifact.committed" in body
    assert '"cached":true' in body
    assert "这是一条已经由真实模型生成并保存的运行结果" in body
    assert "event: subagent.started" not in body


def test_agent_workflow_persists_artifact_for_restart_replay(monkeypatch) -> None:
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    WORKFLOW_ARTIFACTS.clear()
    workflow_artifact_store.clear()

    class FakeStreamClient:
        async def stream_chat(self, messages, temperature=None):  # noqa: ANN001, ARG002
            yield "标题：总览\n摘要：这是一次真实模型返回后的可持久化结果。\n发现：\n- 主题｜敌友问题｜从原文提出问题｜来源：p_mzd_001_0001\n建议点击：\n- 动作｜时间线｜继续探索\n插图提示：无"

    monkeypatch.setattr("app.agents.OpenAICompatibleStreamClient", FakeStreamClient)

    articles = client.get("/api/v1/articles").json()["items"]
    article_id = articles[0]["articleId"]
    release_id = articles[0]["currentReleaseId"]
    article = client.get(f"/api/v1/articles/{article_id}", params={"releaseId": release_id}).json()
    anchor_id = article["anchors"][0]["anchorId"]

    session_response = client.post(
        "/api/v1/reading-sessions",
        json={
            "releaseId": release_id,
            "articleId": article_id,
            "anchorId": anchor_id,
            "mode": "framework_stream",
        },
    )
    session_id = session_response.json()["sessionId"]
    payload = {
        "releaseId": release_id,
        "articleId": article_id,
        "anchorId": anchor_id,
        "workflow": "article_overview",
        "target": {
            "targetType": "article",
            "targetId": article_id,
            "label": "全篇总览",
            "sourceIds": article["anchors"][0]["paragraphIds"],
        },
        "mode": "framework_stream",
        "uiVersion": 7,
        "occurredAt": "2026-06-23T00:00:00Z",
        "forceRegenerate": True,
    }
    cache_key = workflow_cache_key(WorkflowRequest.model_validate(payload))

    workflow_response = client.post(
        f"/api/v1/reading-sessions/{session_id}/workflows",
        headers={"Idempotency-Key": "test-persist-workflow-first"},
        json=payload,
    )
    assert workflow_response.status_code == 202
    assert workflow_response.json()["cached"] is False

    with client.stream("GET", workflow_response.json()["streamUrl"]) as stream_response:
        first_body = "".join(stream_response.iter_text())

    assert "event: workflow.completed" in first_body
    assert workflow_artifact_store.get(cache_key)["artifact"]["text"].startswith("标题：总览")

    WORKFLOW_ARTIFACTS.clear()
    payload["forceRegenerate"] = False
    replay_response = client.post(
        f"/api/v1/reading-sessions/{session_id}/workflows",
        headers={"Idempotency-Key": "test-persist-workflow-replay"},
        json=payload,
    )
    assert replay_response.status_code == 202
    assert replay_response.json()["cached"] is True

    with client.stream("GET", replay_response.json()["streamUrl"]) as stream_response:
        replay_body = "".join(stream_response.iter_text())

    assert '"cached":true' in replay_body
    assert "这是一次真实模型返回后的可持久化结果" in replay_body
    assert "event: subagent.started" not in replay_body


def test_map_workflow_emits_and_replays_map_variables(monkeypatch) -> None:
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    WORKFLOW_ARTIFACTS.clear()
    workflow_artifact_store.clear()

    articles = client.get("/api/v1/articles").json()["items"]
    article_id = articles[0]["articleId"]
    release_id = articles[0]["currentReleaseId"]
    article = client.get(f"/api/v1/articles/{article_id}", params={"releaseId": release_id}).json()
    anchor_id = article["anchors"][0]["anchorId"]
    source_id = article["anchors"][0]["paragraphIds"][0]

    class FakeStreamClient:
        async def stream_chat(self, messages, temperature=None):  # noqa: ANN001, ARG002
            yield (
                "标题：地图语境\n"
                "摘要：这是一次由模型输出地图变量的运行结果。\n"
                "发现：\n"
                f"- 地点｜广州｜原文中可追溯的空间线索｜来源：{source_id}\n"
                "地图变量：\n"
                f"- 地点｜广州｜作为文章语义地图中的地点变量｜来源：{source_id}\n"
                f"- 区域｜阶级分布｜作为文章语义地图中的关系变量｜来源：{source_id}\n"
                "建议点击：\n"
                "- 动作｜继续｜查看上下文\n"
                "插图提示：无"
            )

    monkeypatch.setattr("app.agents.OpenAICompatibleStreamClient", FakeStreamClient)

    session_response = client.post(
        "/api/v1/reading-sessions",
        json={
            "releaseId": release_id,
            "articleId": article_id,
            "anchorId": anchor_id,
            "mode": "framework_stream",
        },
    )
    session_id = session_response.json()["sessionId"]
    payload = {
        "releaseId": release_id,
        "articleId": article_id,
        "anchorId": anchor_id,
        "workflow": "map_context",
        "target": {
            "targetType": "place",
            "targetId": anchor_id,
            "label": "地图语境",
            "sourceIds": article["anchors"][0]["paragraphIds"],
        },
        "mode": "framework_stream",
        "uiVersion": 9,
        "occurredAt": "2026-06-23T00:00:00Z",
        "forceRegenerate": True,
    }
    cache_key = workflow_cache_key(WorkflowRequest.model_validate(payload))

    workflow_response = client.post(
        f"/api/v1/reading-sessions/{session_id}/workflows",
        headers={"Idempotency-Key": "test-map-workflow-first"},
        json=payload,
    )
    assert workflow_response.status_code == 202

    with client.stream("GET", workflow_response.json()["streamUrl"]) as stream_response:
        first_body = "".join(stream_response.iter_text())

    stored = workflow_artifact_store.get(cache_key)
    assert "event: map.variables.committed" in first_body
    assert "广州" in first_body
    assert stored["mapVariables"]["variables"][0]["label"] == "广州"

    WORKFLOW_ARTIFACTS.clear()
    payload["forceRegenerate"] = False
    replay_response = client.post(
        f"/api/v1/reading-sessions/{session_id}/workflows",
        headers={"Idempotency-Key": "test-map-workflow-replay"},
        json=payload,
    )
    assert replay_response.status_code == 202
    assert replay_response.json()["cached"] is True

    with client.stream("GET", replay_response.json()["streamUrl"]) as stream_response:
        replay_body = "".join(stream_response.iter_text())

    assert "event: map.variables.committed" in replay_body
    assert '"cached":true' in replay_body
    assert "event: subagent.started" not in replay_body


def test_illustration_workflow_requires_real_image_api(monkeypatch) -> None:
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("IMAGE_API_KEY", raising=False)

    settings_response = client.put(
        "/api/v1/settings/llm",
        json={
            "baseUrl": "https://api.example.com/v1",
            "model": "unit-test-model",
            "clearApiKey": True,
            "imageModel": "gpt-image-2",
        },
    )
    assert settings_response.status_code == 200

    class FakeStreamClient:
        async def stream_chat(self, messages, temperature=None):  # noqa: ANN001, ARG002
            yield "标题：插图\n摘要：用于测试的提示词。\n发现：\n- 场景｜文本｜说明｜来源：p1\n建议点击：\n- 动作｜继续｜原因\n插图提示：一张克制的历史文献阅读插图"

    monkeypatch.setattr("app.agents.OpenAICompatibleStreamClient", FakeStreamClient)

    articles = client.get("/api/v1/articles").json()["items"]
    article_id = articles[0]["articleId"]
    release_id = articles[0]["currentReleaseId"]
    article = client.get(f"/api/v1/articles/{article_id}", params={"releaseId": release_id}).json()
    anchor_id = article["anchors"][0]["anchorId"]

    session_response = client.post(
        "/api/v1/reading-sessions",
        json={
            "releaseId": release_id,
            "articleId": article_id,
            "anchorId": anchor_id,
            "mode": "framework_stream",
        },
    )
    session_id = session_response.json()["sessionId"]
    workflow_response = client.post(
        f"/api/v1/reading-sessions/{session_id}/workflows",
        headers={"Idempotency-Key": "test-image-api-required"},
        json={
            "releaseId": release_id,
            "articleId": article_id,
            "anchorId": anchor_id,
            "workflow": "illustration_prompt",
            "target": {
                "targetType": "illustration",
                "targetId": anchor_id,
                "label": "插图方案",
                "sourceIds": article["anchors"][0]["paragraphIds"],
            },
            "mode": "framework_stream",
            "uiVersion": 6,
            "occurredAt": "2026-06-22T00:00:00Z",
        },
    )
    assert workflow_response.status_code == 202

    with client.stream("GET", workflow_response.json()["streamUrl"]) as stream_response:
        body = "".join(stream_response.iter_text())

    assert "event: artifact.committed" in body
    assert "event: image.failed" in body
    assert "event: workflow.failed" in body
    assert "Missing required image setting" in body
