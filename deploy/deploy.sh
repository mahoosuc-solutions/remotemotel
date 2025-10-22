#!/bin/bash
# Deployment script for West Bethel Motel Hotel Operator Agent
# Builds and deploys to Google Cloud Run

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}West Bethel Motel - Deployment${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Configuration
PROJECT_ID=${PROJECT_ID:-"westbethel-operator"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="westbethel-operator"

# Parse command line arguments
ENVIRONMENT="production"
BUILD_ONLY=false
DEPLOY_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --project)
            PROJECT_ID="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --build-only)
            BUILD_ONLY=true
            shift
            ;;
        --deploy-only)
            DEPLOY_ONLY=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --project ID      GCP Project ID (default: westbethel-operator)"
            echo "  --region REGION   GCP Region (default: us-central1)"
            echo "  --build-only      Only build the Docker image"
            echo "  --deploy-only     Only deploy (skip build)"
            echo "  --help            Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${YELLOW}Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service: $SERVICE_NAME"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

# Get current git commit
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "local")
IMAGE_TAG="gcr.io/$PROJECT_ID/hotel-operator-agent:$GIT_SHA"
IMAGE_LATEST="gcr.io/$PROJECT_ID/hotel-operator-agent:latest"

if [[ "$DEPLOY_ONLY" == false ]]; then
    # Step 1: Build Docker image
    echo -e "${YELLOW}Step 1: Building Docker image${NC}"
    echo "Image: $IMAGE_TAG"
    echo ""

    docker build \
        -t $IMAGE_TAG \
        -t $IMAGE_LATEST \
        -f Dockerfile.production \
        .

    echo -e "${GREEN}✓ Image built successfully${NC}\n"

    # Step 2: Push to Container Registry
    echo -e "${YELLOW}Step 2: Pushing to Container Registry${NC}"

    docker push $IMAGE_TAG
    docker push $IMAGE_LATEST

    echo -e "${GREEN}✓ Image pushed successfully${NC}\n"
fi

if [[ "$BUILD_ONLY" == true ]]; then
    echo -e "${GREEN}Build complete! Skipping deployment.${NC}"
    exit 0
fi

# Step 3: Deploy to Cloud Run
echo -e "${YELLOW}Step 3: Deploying to Cloud Run${NC}"

# Use the image tag or latest
DEPLOY_IMAGE=${IMAGE_TAG}
if [[ "$DEPLOY_ONLY" == true ]]; then
    DEPLOY_IMAGE=$IMAGE_LATEST
fi

gcloud run deploy $SERVICE_NAME \
    --image $DEPLOY_IMAGE \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --concurrency 80 \
    --min-instances 1 \
    --max-instances 10 \
    --set-env-vars "ENV=production,PROJECT_ID=$PROJECT_ID,REGION=$REGION,HOTEL_NAME=West Bethel Motel,HOTEL_LOCATION=West Bethel, ME" \
    --set-secrets "OPENAI_API_KEY=openai-api-key:latest,TWILIO_ACCOUNT_SID=twilio-account-sid:latest,TWILIO_AUTH_TOKEN=twilio-auth-token:latest,DATABASE_URL=database-url:latest,REDIS_URL=redis-url:latest"

echo -e "${GREEN}✓ Deployed successfully${NC}\n"

# Step 4: Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --format 'value(status.url)')

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${YELLOW}Service URL:${NC} $SERVICE_URL"
echo ""
echo -e "${YELLOW}Health Check:${NC}"
echo "  curl $SERVICE_URL/health"
echo ""
echo -e "${YELLOW}Voice Health Check:${NC}"
echo "  curl $SERVICE_URL/voice/health"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Test health endpoints"
echo "2. Configure Twilio webhooks:"
echo "   Inbound: $SERVICE_URL/voice/twilio/inbound"
echo "   Status:  $SERVICE_URL/voice/twilio/status"
echo "3. Make a test call to +1 (207) 220-3501"
echo ""
echo -e "${GREEN}Ready for production!${NC}"
