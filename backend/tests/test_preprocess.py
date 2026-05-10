from pathlib import Path
from uuid import uuid4

from app.domain import VideoRecord, VideoSourceType
from app.services.preprocess import VideoPreprocessor


def test_preprocess_falls_back_for_missing_source() -> None:
    preprocessor = VideoPreprocessor()
    video = VideoRecord(
        id=uuid4(),
        title="missing.mp4",
        source_type=VideoSourceType.upload,
        source="/path/does/not/exist.mp4",
    )

    try:
        preprocessor._resolve_source_path(video)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Expected missing source to raise FileNotFoundError")


def test_label_generation_covers_edges() -> None:
    assert VideoPreprocessor._label_for_index(0, 4) == "hook"
    assert VideoPreprocessor._label_for_index(3, 4) == "climax"
    assert VideoPreprocessor._label_for_index(1, 4) == "development"


def test_time_to_seconds_parses_common_formats() -> None:
    assert VideoPreprocessor._time_to_seconds("01:02:03.5") == 3723.5
    assert VideoPreprocessor._time_to_seconds("02:03.5") == 123.5
    assert VideoPreprocessor._time_to_seconds("12.5") == 12.5


def test_label_for_time_uses_video_position() -> None:
    assert VideoPreprocessor._label_for_time(1.0, 20.0) == "hook"
    assert VideoPreprocessor._label_for_time(15.0, 20.0) == "climax"
    assert VideoPreprocessor._label_for_time(8.0, 20.0) == "development"
