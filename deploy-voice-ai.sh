#!/bin/bash
# Deploy Voice AI Assistant to Google Cloud Run
# This script builds and deploys the voice AI server to GCP

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${PROJECT_ID:-""}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="voice-ai-assistant"
IMAGE_NAME=""

echo -e "${BLUE}🚀 Deploying Voice AI Assistant to Google Cloud Run${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed${NC}"
    echo "Please install gcloud: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if PROJECT_ID is set
if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}📋 Getting current GCP project...${NC}"
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
    
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}❌ No GCP project configured${NC}"
        echo "Please set your project:"
        echo "  export PROJECT_ID=your-project-id"
        echo "  gcloud config set project your-project-id"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Using GCP project: ${PROJECT_ID}${NC}"
echo -e "${GREEN}✅ Using region: ${REGION}${NC}"

# Check if .env.local exists
if [ ! -f .env.local ]; then
    echo -e "${RED}❌ .env.local file not found${NC}"
    echo "Please ensure .env.local exists with required configuration"
    exit 1
fi

# Source environment to check API key
source .env.local

# If .env.local overrides PROJECT_ID, respect it
if [ -n "$PROJECT_ID" ]; then
    echo -e "${GREEN}✅ Using .env.local project override: ${PROJECT_ID}${NC}"
else
    echo -e "${YELLOW}⚠️  PROJECT_ID not set in .env.local; using gcloud config value${NC}"
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
fi

# Build fully qualified image name with resolved project id
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your-openai-api-key-here" ]; then
    echo -e "${RED}❌ OpenAI API key not configured${NC}"
    echo "Please update OPENAI_API_KEY in .env.local"
    exit 1
fi

echo -e "${GREEN}✅ OpenAI API key configured${NC}"

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required Google Cloud APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    --project=$PROJECT_ID

# Build the Docker image
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
docker build -f Dockerfile.voice -t $IMAGE_NAME .

# Push to Google Container Registry
echo -e "${YELLOW}📤 Pushing image to Container Registry...${NC}"
docker push $IMAGE_NAME

# Update service yaml with project ID
echo -e "${YELLOW}📝 Updating service configuration...${NC}"
sed "s/PROJECT_ID/${PROJECT_ID}/g" voice-ai-service.yaml > voice-ai-service-deploy.yaml

# Deploy to Cloud Run
echo -e "${YELLOW}🚀 Deploying to Cloud Run...${NC}"

# First, deploy with gcloud command for easier environment variable handling
gcloud run deploy $SERVICE_NAME \
    --image=$IMAGE_NAME \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --port=8000 \
    --timeout=3600 \
    --concurrency=100 \
    --cpu=2 \
    --memory=2Gi \
    --execution-environment=gen2 \
    --set-env-vars="ENV=production" \
    --project=$PROJECT_ID

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)' --project=$PROJECT_ID)

if [ -z "$SERVICE_URL" ]; then
    echo -e "${RED}❌ Failed to get service URL${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Voice AI Assistant deployed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Deployment Details:${NC}"
echo "  Service Name: $SERVICE_NAME"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service URL: $SERVICE_URL"
echo ""
echo -e "${BLUE}🔗 Endpoints:${NC}"
echo "  Health Check: $SERVICE_URL/health"
echo "  Twilio Webhook: $SERVICE_URL/incoming-call"
echo "  WebSocket: ${SERVICE_URL/https:/wss:}/media-stream"
echo ""
echo -e "${BLUE}📞 Twilio Configuration:${NC}"
echo "1. Go to Twilio Console: https://console.twilio.com/"
echo "2. Find your phone number: ${TWILIO_PHONE_NUMBER:-[Check .env.local]}"
echo "3. Set 'A CALL COMES IN' webhook to:"
echo -e "   ${YELLOW}$SERVICE_URL/incoming-call${NC}"
echo ""
echo -e "${GREEN}🎉 Ready to test! Call your Twilio number: ${TWILIO_PHONE_NUMBER:-[Check .env.local]}${NC}"

# Test the deployment
echo -e "${YELLOW}🧪 Testing deployment...${NC}"
if curl -s "$SERVICE_URL/health" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}⚠️  Health check failed - check Cloud Run logs${NC}"
fi

# Clean up temporary file
rm -f voice-ai-service-deploy.yaml

echo -e "${BLUE}📊 Monitor your deployment:${NC}"
echo "  Logs: gcloud logs tail cloud-run --project=$PROJECT_ID"
echo "  Console: https://console.cloud.google.com/run?project=$PROJECT_ID"
