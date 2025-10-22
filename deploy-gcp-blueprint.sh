#!/usr/bin/env bash
set -Eeuo pipefail

# Configuration
PROJECT_ID="webemo-dev"
SERVICE_NAME="voice-ai-blueprint"
REGION="us-central1"
REPOSITORY="voice-ai"
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${SERVICE_NAME}"

log() { printf "\033[1;34m==>\033[0m %s\n" "$*"; }
err() { printf "\033[1;31m[ERROR]\033[0m %s\n" "$*" 1>&2; }

# Check if gcloud is installed
command -v gcloud >/dev/null 2>&1 || { err "gcloud CLI required."; exit 1; }

log "Building and pushing Docker image to GCR..."
docker build -f Dockerfile.blueprint -t ${IMAGE_NAME} .
docker push ${IMAGE_NAME}

log "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --port 8000 \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300 \
  --project ${PROJECT_ID}

log "Getting service URL..."
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --format 'value(status.url)')

log "✅ Service deployed successfully!"
log "🌐 Service URL: ${SERVICE_URL}"
log "🏥 Health check: ${SERVICE_URL}/health"