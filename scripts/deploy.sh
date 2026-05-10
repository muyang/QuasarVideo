#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-cpu}"
PROJECT_NAME="${AIVIS_COMPOSE_PROJECT_NAME:-aivis}"

if [ ! -f .env ]; then
  cp .env.example .env
fi

case "$MODE" in
  cpu)
    docker compose -p "$PROJECT_NAME" up -d --build
    ;;
  gpu)
    docker compose -p "$PROJECT_NAME" -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
    ;;
  down)
    docker compose -p "$PROJECT_NAME" -f docker-compose.yml -f docker-compose.gpu.yml down
    ;;
  logs)
    docker compose -p "$PROJECT_NAME" logs -f
    ;;
  *)
    echo "Usage: scripts/deploy.sh [cpu|gpu|down|logs]"
    exit 1
    ;;
esac
