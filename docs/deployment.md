# Deployment

## One Command Local Deploy

```bash
chmod +x scripts/deploy.sh
scripts/deploy.sh cpu
```

Open:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

## GPU Server Deploy

Prerequisites:

- Docker Engine
- Docker Compose plugin
- NVIDIA driver
- NVIDIA Container Toolkit

Run:

```bash
cp .env.example .env
scripts/deploy.sh gpu
```

The GPU override enables NVIDIA runtime reservations for backend and worker containers. Model packages such as Whisper, faster-whisper, PaddleOCR, CLIP, Qwen-VL, or custom GPU services can be added to `backend/Dockerfile` or mounted as separate model-serving containers.

## Operations

```bash
scripts/deploy.sh logs
scripts/deploy.sh down
```

Persistent data is stored in Docker volumes:

- `aivis_uploads`
- `aivis_storage`
