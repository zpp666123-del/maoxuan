from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class WorkflowArtifactStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._lock = Lock()
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_artifacts (
                    cache_key TEXT PRIMARY KEY,
                    artifact_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def get(self, cache_key: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT artifact_json FROM workflow_artifacts WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
        if not row:
            return None
        data = json.loads(row["artifact_json"])
        return data if isinstance(data, dict) else None

    def put(self, cache_key: str, artifact: dict[str, Any]) -> None:
        serialized = json.dumps(artifact, ensure_ascii=False, separators=(",", ":"))
        timestamp = utc_now()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO workflow_artifacts (cache_key, artifact_json, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    artifact_json = excluded.artifact_json,
                    updated_at = excluded.updated_at
                """,
                (cache_key, serialized, timestamp, timestamp),
            )
            connection.commit()

    def load_all(self) -> dict[str, dict[str, Any]]:
        with self._lock, self._connect() as connection:
            rows = connection.execute("SELECT cache_key, artifact_json FROM workflow_artifacts").fetchall()
        result: dict[str, dict[str, Any]] = {}
        for row in rows:
            data = json.loads(row["artifact_json"])
            if isinstance(data, dict):
                result[row["cache_key"]] = data
        return result

    def clear(self) -> None:
        with self._lock, self._connect() as connection:
            connection.execute("DELETE FROM workflow_artifacts")
            connection.commit()


DEFAULT_STORE_PATH = Path(
    os.getenv(
        "WORKFLOW_ARTIFACT_DB",
        Path(__file__).resolve().parents[2] / ".local" / "workflow_artifacts.sqlite3",
    )
)

workflow_artifact_store = WorkflowArtifactStore(DEFAULT_STORE_PATH)
