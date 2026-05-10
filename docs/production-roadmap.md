# AIVIS Production Roadmap

## Database

- Current MVP uses SQLite JSON payload storage.
- Production target should move to PostgreSQL with separate `videos`, `scenes`, `analyses`, `agents`, and `exports` tables.
- Vector storage can be PostgreSQL `pgvector`, Qdrant, Milvus, or Weaviate.

## Model Integrations

- ASR: Whisper Large-v3 or faster-whisper.
- OCR: PaddleOCR or Tesseract.
- Visual embedding: CLIP, Qwen-VL embedding, or VideoMAE.
- Multimodal reasoning: GPT-5 / Gemini / Qwen-VL / Claude depending on context size.

## Deployment

- API: FastAPI behind reverse proxy.
- Queue: Celery + Redis.
- Worker: GPU-enabled processing workers.
- Storage: S3-compatible object storage for videos, frames, and audio.
