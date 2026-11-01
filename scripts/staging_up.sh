#!/usr/bin/env bash
# Raise staging stack and optionally attach API to Ollama network.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ENV_FILE="${ENV_FILE:-.env.staging}"
OLLAMA_NET="${OLLAMA_DOCKER_NETWORK:-ai-team_default}"
COMPOSE=(docker compose -f docker-compose.staging.yml --env-file "$ENV_FILE")

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE — copy from .env.staging.example" >&2
  exit 1
fi

USE_OLLAMA=0
if docker network inspect "$OLLAMA_NET" >/dev/null 2>&1; then
  USE_OLLAMA=1
  COMPOSE=(docker compose -f docker-compose.staging.yml -f docker-compose.staging.ollama.yml --env-file "$ENV_FILE")
  echo "Ollama network '$OLLAMA_NET' found — using staging.ollama override"
else
  echo "Ollama network '$OLLAMA_NET' not found — starting without LLM network attach"
fi

"${COMPOSE[@]}" up -d --build

# Fallback if override was not used but network appeared later
if [[ "$USE_OLLAMA" -eq 0 ]] && docker network inspect "$OLLAMA_NET" >/dev/null 2>&1; then
  docker network connect "$OLLAMA_NET" mwe-staging-api 2>/dev/null || true
fi

# If override used, recreate may still need connect after some compose versions
if [[ "$USE_OLLAMA" -eq 1 ]]; then
  docker network connect "$OLLAMA_NET" mwe-staging-api 2>/dev/null || true
fi

echo "--- health ---"
curl -fsS http://127.0.0.1:8001/health
echo
curl -fsSI http://127.0.0.1:3001/ | head -n 1 || true
echo "--- done ---"
