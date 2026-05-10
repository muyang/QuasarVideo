from uuid import uuid4

from app.domain import AnalysisTask, TaskStatus, VideoRecord, VideoSourceType
from app.store import SQLiteStore


def test_sqlite_store_persists_entities(tmp_path) -> None:
    store = SQLiteStore(tmp_path / "aivis.db")
    video = VideoRecord(
        id=uuid4(),
        title="sample.mp4",
        source_type=VideoSourceType.upload,
        source="/tmp/sample.mp4",
    )
    task = AnalysisTask(video=video, status=TaskStatus.completed)

    store.save_video(video)
    store.save_task(task)

    loaded_video = store.get_video(video.id)
    loaded_task = store.get_task(task.id)

    assert loaded_video is not None
    assert loaded_video.title == video.title
    assert loaded_task is not None
    assert loaded_task.status == TaskStatus.completed
