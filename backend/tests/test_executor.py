from unittest.mock import Mock, patch

from app.config import get_settings
from app.domain import AnalysisTask, VideoRecord, VideoSourceType
from app.services.executor import BackgroundTaskExecutor, CeleryTaskExecutor, create_task_executor


def test_create_task_executor_defaults_to_background(monkeypatch) -> None:
    monkeypatch.delenv("AIVIS_TASK_EXECUTOR", raising=False)
    get_settings.cache_clear()
    create_task_executor.cache_clear()

    executor = create_task_executor()

    assert isinstance(executor, BackgroundTaskExecutor)


def test_create_task_executor_can_select_celery(monkeypatch) -> None:
    monkeypatch.setenv("AIVIS_TASK_EXECUTOR", "celery")
    get_settings.cache_clear()
    create_task_executor.cache_clear()

    executor = create_task_executor()

    assert isinstance(executor, CeleryTaskExecutor)


def test_celery_executor_submits_named_task() -> None:
    video = VideoRecord(title="sample.mp4", source_type=VideoSourceType.url, source="https://example.com")
    task = AnalysisTask(video=video)
    celery_app = Mock()

    with patch("app.celery_app.celery_app", celery_app):
        CeleryTaskExecutor().submit(Mock(), task)

    celery_app.send_task.assert_called_once_with("app.tasks.run_analysis_task", args=[str(task.id)])
