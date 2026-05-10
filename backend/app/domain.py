from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl


class TaskStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class VideoSourceType(str, Enum):
    upload = "upload"
    url = "url"


class VideoRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    source_type: VideoSourceType
    source: str
    platform: str | None = None
    duration: float | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AnalyzeRequest(BaseModel):
    video_id: UUID | None = None
    url: HttpUrl | None = None
    platform: str | None = None
    title: str | None = None


class AnalyzeResponse(BaseModel):
    id: UUID
    status: TaskStatus


class UploadResponse(BaseModel):
    video_id: UUID
    title: str


class Scene(BaseModel):
    start: float
    end: float
    label: str


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class OCRLine(BaseModel):
    frame: str
    text: str
    confidence: float


class VisualEmbedding(BaseModel):
    frame: str
    vector: list[float]


class TimelineEntry(BaseModel):
    start: float
    end: float
    scene_label: str
    transcript: str
    recommendation: str


class SimilarCase(BaseModel):
    title: str
    platform: str
    similarity: float
    reason: str


class DNASignature(BaseModel):
    hook_strength: str
    pacing: str
    emotion_pattern: str
    visual_pattern: str


class PreprocessResult(BaseModel):
    video_id: UUID
    source_path: str
    duration: float | None
    frame_directory: str | None
    audio_path: str | None
    frames_sampled: int
    scenes: list[Scene]
    transcript: list[TranscriptSegment]
    ocr: list[OCRLine]
    visual_embeddings: list[VisualEmbedding]
    audio_profile: dict[str, float | str]
    capabilities: dict[str, bool]
    warnings: list[str] = Field(default_factory=list)


class AgentResult(BaseModel):
    name: str
    output: dict


class AnalysisReport(BaseModel):
    overview: dict
    topic: dict
    script: dict
    director: dict
    editing: dict
    emotion: dict
    marketing: dict
    timeline: list[TimelineEntry]
    dna: DNASignature
    similar_cases: list[SimilarCase]
    recommendations: list[str]
    agent_results: list[AgentResult]


class AnalysisTask(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    video: VideoRecord
    status: TaskStatus = TaskStatus.queued
    report: AnalysisReport | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
