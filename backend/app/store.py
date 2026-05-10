from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from uuid import UUID

from app.config import get_settings
from app.domain import AnalysisTask, VideoRecord


class SQLiteStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.lock = Lock()
        self._initialize()

    def save_video(self, video: VideoRecord) -> VideoRecord:
        payload = video.model_dump(mode="json")
        with self.lock, self.connection() as conn:
            conn.execute(
                """
                INSERT INTO videos (id, payload)
                VALUES (?, ?)
                ON CONFLICT(id) DO UPDATE SET payload=excluded.payload
                """,
                (str(video.id), json.dumps(payload, ensure_ascii=False)),
            )
            conn.commit()
        return video

    def get_video(self, video_id: UUID) -> VideoRecord | None:
        with self.connection() as conn:
            row = conn.execute("SELECT payload FROM videos WHERE id = ?", (str(video_id),)).fetchone()
        if row is None:
            return None
        return VideoRecord.model_validate(json.loads(row[0]))

    def save_task(self, task: AnalysisTask) -> AnalysisTask:
        payload = task.model_dump(mode="json")
        with self.lock, self.connection() as conn:
            conn.execute(
                """
                INSERT INTO tasks (id, payload)
                VALUES (?, ?)
                ON CONFLICT(id) DO UPDATE SET payload=excluded.payload
                """,
                (str(task.id), json.dumps(payload, ensure_ascii=False)),
            )
            conn.commit()
        return task

    def get_task(self, task_id: UUID) -> AnalysisTask | None:
        with self.connection() as conn:
            row = conn.execute("SELECT payload FROM tasks WHERE id = ?", (str(task_id),)).fetchone()
        if row is None:
            return None
        return AnalysisTask.model_validate(json.loads(row[0]))

    def list_tasks(self) -> list[AnalysisTask]:
        with self.connection() as conn:
            rows = conn.execute("SELECT payload FROM tasks ORDER BY rowid DESC").fetchall()
        return [AnalysisTask.model_validate(json.loads(row[0])) for row in rows]

    def list_videos(self) -> list[VideoRecord]:
        with self.connection() as conn:
            rows = conn.execute("SELECT payload FROM videos ORDER BY rowid DESC").fetchall()
        return [VideoRecord.model_validate(json.loads(row[0])) for row in rows]


    def _initialize(self) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS videos (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.commit()

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()


store = SQLiteStore(get_settings().database_path)
