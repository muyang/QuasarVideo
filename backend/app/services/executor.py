from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache

from fastapi import BackgroundTasks

from app.config import get_settings
from app.domain import AnalysisTask
from app.services.pipeline import pipeline


class TaskExecutor(ABC):
    @abstractmethod
    def submit(self, background_tasks: BackgroundTasks, task: AnalysisTask) -> None:
        raise NotImplementedError


class BackgroundTaskExecutor(TaskExecutor):
    def submit(self, background_tasks: BackgroundTasks, task: AnalysisTask) -> None:
        background_tasks.add_task(pipeline.run, task)


class CeleryTaskExecutor(TaskExecutor):
    def submit(self, background_tasks: BackgroundTasks, task: AnalysisTask) -> None:
        from app.celery_app import celery_app

        celery_app.send_task("app.tasks.run_analysis_task", args=[str(task.id)])


@lru_cache
def create_task_executor() -> TaskExecutor:
    settings = get_settings()
    if settings.task_executor == "celery":
        return CeleryTaskExecutor()
    return BackgroundTaskExecutor()


task_executor = create_task_executor()
