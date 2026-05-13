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

### GPU Server Test Checklist

1. Verify GPU and container runtime prerequisites:

```bash
nvidia-smi
docker --version
docker compose version
```

The server should have NVIDIA Driver, NVIDIA Container Toolkit, Docker, and Docker Compose plugin installed.

2. Clone the release and start GPU mode:

```bash
git clone git@github.com:muyang/QuasarVideo.git
cd QuasarVideo
cp .env.example .env
scripts/deploy.sh gpu
```

3. Confirm backend and worker containers can see the GPU:

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml exec backend nvidia-smi
docker compose -f docker-compose.yml -f docker-compose.gpu.yml exec worker nvidia-smi
```

4. Features testable in the current release:

- Docker GPU deployment path.
- Redis + Celery asynchronous task execution.
- Video upload and persistent storage.
- FFmpeg frame extraction.
- FFprobe duration/metadata extraction.
- FFmpeg audio extraction.
- Tesseract basic OCR.
- Report generation and JSON / Markdown / HTML export.
- Capability and warning inspection in report `overview`.

5. After uploading a real video, inspect these report fields:

- `overview.duration`: should match the real video duration.
- `overview.frame_directory`: should be populated when FFmpeg works.
- `overview.audio_path`: should be populated when audio extraction works.
- `overview.frames_sampled`: should be greater than `0`.
- `overview.ocr_lines`: should increase when OCR detects text.
- `overview.capabilities.ffmpeg`: should be `true`.
- `overview.capabilities.ffprobe`: should be `true`.
- `overview.capabilities.tesseract`: should be `true`.
- `overview.warnings`: should shrink as tools become available.

6. Features not fully enabled yet without more model integrations:

- Whisper / faster-whisper ASR.
- GPU OCR.
- Scene detection with `scenedetect`.
- CLIP / Qwen-VL visual understanding.
- Qdrant / Milvus / pgvector vector search.
- LLM-generated director-level report.

7. Minimal next unlock on the GPU server:

```bash
pip install faster-whisper scenedetect
```

For repeatable deployment, prefer adding these dependencies to `backend/Dockerfile` instead of installing them manually inside a running container. The recommended next development step is to integrate `faster-whisper` through the Python SDK, add `scenedetect`, and write real ASR results into `PreprocessResult.transcript`.

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
