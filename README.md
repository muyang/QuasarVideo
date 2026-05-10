# AIVIS - AI Video Intelligence System

AIVIS is an AI multimodal video analysis system. This repository currently contains an MVP engineering scaffold based on `AI视频分析系统（AI Video Intelligence System）.md`.

## Modules

- `backend`: FastAPI API service, analysis workflow, agent interfaces, report generation.
- `frontend`: Next.js dashboard for video upload/URL submission and report viewing.

## Quick Start

### Docker One-Command Deploy

```bash
chmod +x scripts/deploy.sh
scripts/deploy.sh cpu
```

GPU server mode:

```bash
scripts/deploy.sh gpu
```

See `docs/deployment.md` for GPU deployment notes.

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` and ensure the backend is running at `http://localhost:8000`.

## API

- `POST /api/v1/video/upload`: upload a local video file.
- `POST /api/v1/analyze`: create an analysis task from an uploaded `video_id` or a remote URL.
- `GET /api/v1/report/{id}`: get task status and generated report.
- `GET /api/v1/tasks`: list recent analysis tasks.
- `GET /api/v1/videos`: list known videos.

## Task Execution

The backend supports two task execution modes:

- `AIVIS_TASK_EXECUTOR=background`: default FastAPI background task mode for local development.
- `AIVIS_TASK_EXECUTOR=celery`: Redis-backed Celery worker mode for production-like runs.

Run the full stack with Redis and a worker:

```bash
docker compose up
```

## Current Scope

The initial implementation focuses on a working system boundary and extensible domain structure. Heavy AI/video processing components such as FFmpeg, Whisper, scene detection, CLIP/Qwen embeddings, RAG, and model orchestration are represented by replaceable service classes and deterministic placeholder output.
