#!/bin/bash
# Setup script for Google Cloud Platform infrastructure
# West Bethel Motel - Hotel Operator Agent

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}West Bethel Motel - GCP Setup${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Configuration
PROJECT_ID="westbethel-operator"
REGION="us-central1"
SERVICE_NAME="westbethel-operator"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Step 1: Set project
echo -e "${YELLOW}Step 1: Setting GCP project${NC}"
read -p "Enter your GCP Project ID [default: $PROJECT_ID]: " input_project
PROJECT_ID="${input_project:-$PROJECT_ID}"

gcloud config set project $PROJECT_ID
echo -e "${GREEN}✓ Project set to: $PROJECT_ID${NC}\n"

# Step 2: Enable required APIs
echo -e "${YELLOW}Step 2: Enabling required APIs${NC}"
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com \
    sql-component.googleapis.com \
    sqladmin.googleapis.com \
    redis.googleapis.com \
    storage-component.googleapis.com \
    storage-api.googleapis.com \
    cloudtrace.googleapis.com \
    monitoring.googleapis.com \
    logging.googleapis.com

echo -e "${GREEN}✓ APIs enabled${NC}\n"

# Step 3: Create secrets in Secret Manager
echo -e "${YELLOW}Step 3: Creating secrets in Secret Manager${NC}"

create_secret() {
    local secret_name=$1
    local secret_description=$2

    echo -e "Creating secret: ${GREEN}$secret_name${NC}"
    echo -n "$secret_description"
    read -s secret_value
    echo

    # Check if secret exists
    if gcloud secrets describe $secret_name --project=$PROJECT_ID &>/dev/null; then
        echo -e "${YELLOW}Secret $secret_name already exists, creating new version${NC}"
        echo -n "$secret_value" | gcloud secrets versions add $secret_name --data-file=-
    else
        echo -n "$secret_value" | gcloud secrets create $secret_name \
            --data-file=- \
            --replication-policy="automatic"
    fi

    echo -e "${GREEN}✓ Secret $secret_name created/updated${NC}\n"
}

create_secret "openai-api-key" "Enter your OpenAI API key: "
create_secret "twilio-account-sid" "Enter your Twilio Account SID: "
create_secret "twilio-auth-token" "Enter your Twilio Auth Token: "

# Step 4: Create Cloud Storage bucket for recordings
echo -e "${YELLOW}Step 4: Creating Cloud Storage bucket${NC}"
BUCKET_NAME="westbethel-voice-recordings"
if gsutil ls -b gs://$BUCKET_NAME &>/dev/null; then
    echo -e "${YELLOW}Bucket already exists${NC}"
else
    gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$BUCKET_NAME
    echo -e "${GREEN}✓ Bucket created: gs://$BUCKET_NAME${NC}"
fi
echo

# Step 5: Create Cloud SQL instance (optional - can use SQLite for now)
echo -e "${YELLOW}Step 5: Cloud SQL setup${NC}"
read -p "Do you want to create a Cloud SQL PostgreSQL instance? (y/n) [n]: " create_sql
if [[ "$create_sql" == "y" ]]; then
    SQL_INSTANCE="westbethel-db"
    echo "Creating Cloud SQL instance (this may take 5-10 minutes)..."

    gcloud sql instances create $SQL_INSTANCE \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=$REGION \
        --storage-type=SSD \
        --storage-size=10GB \
        --backup \
        --backup-start-time=03:00 \
        --maintenance-window-day=SUN \
        --maintenance-window-hour=04 \
        --availability-type=zonal

    # Create database
    gcloud sql databases create operator_db --instance=$SQL_INSTANCE

    # Create user
    DB_PASSWORD=$(openssl rand -base64 32)
    gcloud sql users create operator \
        --instance=$SQL_INSTANCE \
        --password=$DB_PASSWORD

    # Get connection name
    CONNECTION_NAME=$(gcloud sql instances describe $SQL_INSTANCE --format='value(connectionName)')

    # Store database URL in secrets
    DATABASE_URL="postgresql://operator:$DB_PASSWORD@/$SQL_INSTANCE?host=/cloudsql/$CONNECTION_NAME"
    echo -n "$DATABASE_URL" | gcloud secrets create database-url \
        --data-file=- \
        --replication-policy="automatic"

    echo -e "${GREEN}✓ Cloud SQL instance created${NC}"
    echo -e "${YELLOW}Connection name: $CONNECTION_NAME${NC}"
else
    echo -e "${YELLOW}Skipping Cloud SQL setup${NC}"
    # Create dummy secret for DATABASE_URL
    echo -n "sqlite:///./operator.db" | gcloud secrets create database-url \
        --data-file=- \
        --replication-policy="automatic" 2>/dev/null || true
fi
echo

# Step 6: Create Redis instance (optional)
echo -e "${YELLOW}Step 6: Redis (Memorystore) setup${NC}"
read -p "Do you want to create a Redis instance? (y/n) [n]: " create_redis
if [[ "$create_redis" == "y" ]]; then
    REDIS_INSTANCE="westbethel-redis"
    echo "Creating Redis instance (this may take 5-10 minutes)..."

    gcloud redis instances create $REDIS_INSTANCE \
        --size=1 \
        --region=$REGION \
        --redis-version=redis_6_x \
        --tier=basic

    # Get Redis host and port
    REDIS_HOST=$(gcloud redis instances describe $REDIS_INSTANCE --region=$REGION --format='value(host)')
    REDIS_PORT=$(gcloud redis instances describe $REDIS_INSTANCE --region=$REGION --format='value(port)')

    # Store Redis URL in secrets
    REDIS_URL="redis://$REDIS_HOST:$REDIS_PORT"
    echo -n "$REDIS_URL" | gcloud secrets create redis-url \
        --data-file=- \
        --replication-policy="automatic"

    echo -e "${GREEN}✓ Redis instance created${NC}"
else
    echo -e "${YELLOW}Skipping Redis setup${NC}"
    # Create dummy secret for REDIS_URL
    echo -n "redis://localhost:6379" | gcloud secrets create redis-url \
        --data-file=- \
        --replication-policy="automatic" 2>/dev/null || true
fi
echo

# Step 7: Grant Cloud Run access to secrets
echo -e "${YELLOW}Step 7: Granting permissions${NC}"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

for secret in openai-api-key twilio-account-sid twilio-auth-token database-url redis-url; do
    gcloud secrets add-iam-policy-binding $secret \
        --member="serviceAccount:$COMPUTE_SA" \
        --role="roles/secretmanager.secretAccessor" \
        --project=$PROJECT_ID
done

echo -e "${GREEN}✓ Permissions granted${NC}\n"

# Step 8: Create service account for Cloud Run
echo -e "${YELLOW}Step 8: Creating service account${NC}"
SERVICE_ACCOUNT="westbethel-sa"
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com"

if gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL &>/dev/null; then
    echo -e "${YELLOW}Service account already exists${NC}"
else
    gcloud iam service-accounts create $SERVICE_ACCOUNT \
        --display-name="West Bethel Motel Operator Service Account"

    # Grant necessary roles
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/cloudsql.client"

    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/storage.objectAdmin"

    echo -e "${GREEN}✓ Service account created${NC}"
fi
echo

# Step 9: Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service Name: $SERVICE_NAME"
echo "Storage Bucket: gs://$BUCKET_NAME"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Run ./deploy/deploy.sh to build and deploy"
echo "2. Configure Twilio webhooks to point to your Cloud Run URL"
echo "3. Test with a phone call"
echo ""
echo -e "${GREEN}Infrastructure is ready!${NC}"
