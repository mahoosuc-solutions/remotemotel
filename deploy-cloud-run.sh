#!/usr/bin/env bash
set -Eeuo pipefail

# Parse command line arguments
DOCKERFILE="Dockerfile"
while [[ $# -gt 0 ]]; do
  case $1 in
    -f)
      DOCKERFILE="$2"
      shift 2
      ;;
    *)
      break
      ;;
  esac
done

PROJECT_ID=${PROJECT_ID:-"local-test-project"}
SERVICE_NAME=${SERVICE_NAME:-"hotel-operator-agent"}
IMAGE=${IMAGE:-"${SERVICE_NAME}:local"}
PORT=${PORT:-8000}
log() { printf "\033[1;34m==>\033[0m %s\n" "$*"; }
err() { printf "\033[1;31m[ERROR]\033[0m %s\n" "$*" 1>&2; }
command -v docker >/dev/null 2>&1 || { err "Docker required."; exit 1; }
log "Building local Docker image using ${DOCKERFILE}..."
docker build -f ${DOCKERFILE} -t ${IMAGE} .
log "Running local container on port ${PORT}..."
docker run --rm -it -p ${PORT}:8000 \
  -e ENV=local -e PROJECT_ID=${PROJECT_ID} \
  -e SUPABASE_FORCE=true \
  ${IMAGE}
