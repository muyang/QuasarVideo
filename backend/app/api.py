from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Response, UploadFile, status

from app.config import get_settings
from app.domain import (
    AnalysisTask,
    AnalyzeRequest,
    AnalyzeResponse,
    UploadResponse,
    VideoRecord,
    VideoSourceType,
)
from app.services.executor import task_executor
from app.services.report import ReportGenerator
from app.store import store

router = APIRouter(prefix="/api/v1")
report_generator = ReportGenerator()


@router.post("/video/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    settings = get_settings()
    safe_name = Path(file.filename).name
    video = VideoRecord(title=safe_name, source_type=VideoSourceType.upload, source=safe_name)
    destination = settings.upload_dir / f"{video.id}-{safe_name}"

    content = await file.read()
    destination.write_bytes(content)
    video.source = str(destination)
    store.save_video(video)
    return UploadResponse(video_id=video.id, title=video.title)


@router.post("/analyze", response_model=AnalyzeResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_analysis(request: AnalyzeRequest, background_tasks: BackgroundTasks) -> AnalyzeResponse:
    if request.video_id is None and request.url is None:
        raise HTTPException(status_code=400, detail="Provide either video_id or url")

    if request.video_id is not None:
        video = store.get_video(request.video_id)
        if video is None:
            raise HTTPException(status_code=404, detail="Video not found")
        if request.platform:
            video.platform = request.platform
    else:
        url = str(request.url)
        video = VideoRecord(
            title=request.title or url,
            source_type=VideoSourceType.url,
            source=url,
            platform=request.platform,
        )
        store.save_video(video)

    task = store.save_task(AnalysisTask(video=video))
    task_executor.submit(background_tasks, task)
    return AnalyzeResponse(id=task.id, status=task.status)


@router.get("/report/{task_id}", response_model=AnalysisTask)
async def get_report(task_id: UUID) -> AnalysisTask:
    task = store.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return task


@router.get("/tasks", response_model=list[AnalysisTask])
async def list_tasks() -> list[AnalysisTask]:
    return store.list_tasks()


@router.get("/videos", response_model=list[VideoRecord])
async def list_videos() -> list[VideoRecord]:
    return store.list_videos()


@router.get("/report/{task_id}/export")
async def export_report(task_id: UUID) -> dict:
    task = store.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Report not found")
    if task.report is None:
        raise HTTPException(status_code=409, detail="Report is not ready")
    return {
        "task_id": str(task.id),
        "video_id": str(task.video.id),
        "report": json.loads(task.report.model_dump_json()),
    }


@router.get("/report/{task_id}/export.md")
async def export_report_markdown(task_id: UUID) -> Response:
    task = store.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Report not found")
    if task.report is None:
        raise HTTPException(status_code=409, detail="Report is not ready")

    markdown = report_generator.to_markdown(task)
    return Response(
        content=markdown,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="aivis-report-{task_id}.md"'
        },
    )


@router.get("/report/{task_id}/export.html")
async def export_report_html(task_id: UUID) -> Response:
    task = store.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Report not found")
    if task.report is None:
        raise HTTPException(status_code=409, detail="Report is not ready")

    html = report_generator.to_html(task)
    return Response(
        content=html,
        media_type="text/html; charset=utf-8",
        headers={
            "Content-Disposition": f'inline; filename="aivis-report-{task_id}.html"'
        },
    )
