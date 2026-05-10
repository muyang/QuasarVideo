from __future__ import annotations

import asyncio
from uuid import UUID

from app.celery_app import celery_app
from app.services.pipeline import pipeline
from app.store import store


@celery_app.task(name="app.tasks.run_analysis_task")
def run_analysis_task(task_id: str) -> None:
    task = store.get_task(UUID(task_id))
    if task is None:
        raise ValueError(f"Analysis task not found: {task_id}")
    asyncio.run(pipeline.run(task))
