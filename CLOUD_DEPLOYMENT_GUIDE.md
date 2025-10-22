# Cloud Deployment Guide
## West Bethel Motel - Hotel Operator Agent

**Platform**: Google Cloud Run
**Date**: 2025-10-17
**Status**: Production-Ready

---

## Overview

This guide walks you through deploying the West Bethel Motel Hotel Operator Agent to Google Cloud Platform using Cloud Run. The deployment includes:

- **Cloud Run**: Serverless container platform for the application
- **Secret Manager**: Secure storage for API keys and credentials
- **Cloud Storage**: Voice recording storage
- **Cloud SQL** (optional): PostgreSQL database
- **Redis/Memorystore** (optional): Caching layer
- **Cloud Build**: CI/CD pipeline

---

## Prerequisites

### 1. Google Cloud Account
- Create account at: https://cloud.google.com
- Enable billing
- Install gcloud CLI: https://cloud.google.com/sdk/docs/install

### 2. Required Tools
```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Install Docker
# macOS: Download Docker Desktop
# Linux: https://docs.docker.com/engine/install/

# Verify installations
gcloud --version
docker --version
git --version
```

### 3. API Keys
- OpenAI API Key (with Realtime API access)
- Twilio Account (Account SID, Auth Token, Phone Number)

---

## Quick Start (5 Minutes)

### Step 1: Clone and Navigate
```bash
cd /home/webemo-aaron/projects/front-desk
```

### Step 2: Run GCP Setup Script
```bash
./deploy/setup-gcp.sh
```

This script will:
- ✅ Create GCP project (or use existing)
- ✅ Enable required APIs
- ✅ Create secrets in Secret Manager
- ✅ Set up Cloud Storage bucket
- ✅ Configure permissions
- ✅ Create service account

**You'll be prompted for**:
- Project ID (default: westbethel-operator)
- OpenAI API key
- Twilio credentials
- Cloud SQL setup (optional)
- Redis setup (optional)

### Step 3: Deploy to Cloud Run
```bash
./deploy/deploy.sh
```

This script will:
- ✅ Build Docker image
- ✅ Push to Container Registry
- ✅ Deploy to Cloud Run
- ✅ Configure environment variables
- ✅ Inject secrets
- ✅ Return service URL

### Step 4: Configure Twilio Webhooks
```bash
# Get your service URL from deploy output
SERVICE_URL="https://westbethel-operator-xxxxx.run.app"

# Configure in Twilio Console:
# Inbound: $SERVICE_URL/voice/twilio/inbound
# Status:  $SERVICE_URL/voice/twilio/status
```

### Step 5: Test
```bash
# Health check
curl https://westbethel-operator-xxxxx.run.app/health

# Make a phone call
# Call: +1 (207) 220-3501
```

---

## Detailed Setup

### 1. GCP Project Setup

#### Create Project
```bash
# Create new project
gcloud projects create westbethel-operator \
    --name="West Bethel Motel Operator"

# Set as default
gcloud config set project westbethel-operator

# Link billing account
gcloud billing projects link westbethel-operator \
    --billing-account=BILLING_ACCOUNT_ID
```

#### Enable APIs
```bash
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
```

### 2. Secret Manager Configuration

#### Create Secrets
```bash
# OpenAI API Key
echo -n "sk-your-openai-key" | gcloud secrets create openai-api-key \
    --data-file=- \
    --replication-policy="automatic"

# Twilio Account SID
echo -n "ACxxxxxx" | gcloud secrets create twilio-account-sid \
    --data-file=- \
    --replication-policy="automatic"

# Twilio Auth Token
echo -n "your-auth-token" | gcloud secrets create twilio-auth-token \
    --data-file=- \
    --replication-policy="automatic"

# Database URL (if using Cloud SQL)
echo -n "postgresql://..." | gcloud secrets create database-url \
    --data-file=- \
    --replication-policy="automatic"

# Redis URL (if using Memorystore)
echo -n "redis://..." | gcloud secrets create redis-url \
    --data-file=- \
    --replication-policy="automatic"
```

#### Grant Access to Secrets
```bash
PROJECT_NUMBER=$(gcloud projects describe westbethel-operator --format='value(projectNumber)')
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

for secret in openai-api-key twilio-account-sid twilio-auth-token database-url redis-url; do
    gcloud secrets add-iam-policy-binding $secret \
        --member="serviceAccount:$COMPUTE_SA" \
        --role="roles/secretmanager.secretAccessor"
done
```

### 3. Cloud Storage Setup

#### Create Bucket for Recordings
```bash
gsutil mb -p westbethel-operator \
    -c STANDARD \
    -l us-central1 \
    gs://westbethel-voice-recordings

# Set lifecycle policy (delete after 90 days)
cat > lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [{
      "action": {"type": "Delete"},
      "condition": {"age": 90}
    }]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://westbethel-voice-recordings
```

### 4. Cloud SQL Setup (Optional)

#### Create PostgreSQL Instance
```bash
gcloud sql instances create westbethel-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --storage-type=SSD \
    --storage-size=10GB \
    --backup \
    --backup-start-time=03:00 \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=04 \
    --availability-type=zonal
```

#### Create Database and User
```bash
# Create database
gcloud sql databases create operator_db --instance=westbethel-db

# Create user
DB_PASSWORD=$(openssl rand -base64 32)
gcloud sql users create operator \
    --instance=westbethel-db \
    --password=$DB_PASSWORD

# Get connection name
CONNECTION_NAME=$(gcloud sql instances describe westbethel-db --format='value(connectionName)')

# Create secret with database URL
DATABASE_URL="postgresql://operator:$DB_PASSWORD@/$CONNECTION_NAME?host=/cloudsql/$CONNECTION_NAME"
echo -n "$DATABASE_URL" | gcloud secrets create database-url \
    --data-file=- \
    --replication-policy="automatic"
```

### 5. Redis/Memorystore Setup (Optional)

#### Create Redis Instance
```bash
gcloud redis instances create westbethel-redis \
    --size=1 \
    --region=us-central1 \
    --redis-version=redis_6_x \
    --tier=basic

# Get connection info
REDIS_HOST=$(gcloud redis instances describe westbethel-redis --region=us-central1 --format='value(host)')
REDIS_PORT=$(gcloud redis instances describe westbethel-redis --region=us-central1 --format='value(port)')

# Create secret
REDIS_URL="redis://$REDIS_HOST:$REDIS_PORT"
echo -n "$REDIS_URL" | gcloud secrets create redis-url \
    --data-file=- \
    --replication-policy="automatic"
```

---

## Deployment Options

### Option 1: Manual Deployment (One-Time)

```bash
# Build image
docker build -t gcr.io/westbethel-operator/hotel-operator-agent:latest \
    -f Dockerfile.production .

# Push to registry
docker push gcr.io/westbethel-operator/hotel-operator-agent:latest

# Deploy to Cloud Run
gcloud run deploy westbethel-operator \
    --image gcr.io/westbethel-operator/hotel-operator-agent:latest \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --concurrency 80 \
    --min-instances 1 \
    --max-instances 10 \
    --set-env-vars "ENV=production,PROJECT_ID=westbethel-operator" \
    --set-secrets "OPENAI_API_KEY=openai-api-key:latest,TWILIO_ACCOUNT_SID=twilio-account-sid:latest,TWILIO_AUTH_TOKEN=twilio-auth-token:latest"
```

### Option 2: Using Deployment Script

```bash
# Full deployment
./deploy/deploy.sh

# Custom project and region
./deploy/deploy.sh --project my-project --region us-west1

# Build only (no deploy)
./deploy/deploy.sh --build-only

# Deploy only (skip build)
./deploy/deploy.sh --deploy-only
```

### Option 3: CI/CD with Cloud Build

#### Setup Cloud Build Trigger
```bash
# Connect GitHub repository
gcloud beta builds triggers create github \
    --repo-name=front-desk \
    --repo-owner=webemo-aaron \
    --branch-pattern="^main$" \
    --build-config=cloudbuild.yaml

# Manual trigger
gcloud builds submit --config=cloudbuild.yaml .
```

#### Continuous Deployment
Every push to `main` branch will automatically:
1. Build Docker image
2. Push to Container Registry
3. Deploy to Cloud Run
4. Run health checks

---

## Configuration

### Environment Variables

**Set in Cloud Run**:
```bash
gcloud run services update westbethel-operator \
    --region us-central1 \
    --set-env-vars "
        ENV=production,
        PROJECT_ID=westbethel-operator,
        HOTEL_NAME=West Bethel Motel,
        HOTEL_LOCATION=West Bethel, ME,
        OPENAI_REALTIME_ENABLED=true,
        MAX_CALL_DURATION_MINUTES=10
    "
```

### Secrets (Injected at Runtime)

Secrets are stored in Secret Manager and injected as environment variables:
- `OPENAI_API_KEY` → openai-api-key:latest
- `TWILIO_ACCOUNT_SID` → twilio-account-sid:latest
- `TWILIO_AUTH_TOKEN` → twilio-auth-token:latest
- `DATABASE_URL` → database-url:latest
- `REDIS_URL` → redis-url:latest

### Update Secret
```bash
# Update OpenAI API key
echo -n "new-api-key" | gcloud secrets versions add openai-api-key --data-file=-

# Redeploy to pick up new secret
gcloud run services update westbethel-operator \
    --region us-central1 \
    --update-secrets "OPENAI_API_KEY=openai-api-key:latest"
```

---

## Twilio Integration

### Get Service URL
```bash
SERVICE_URL=$(gcloud run services describe westbethel-operator \
    --region us-central1 \
    --format 'value(status.url)')

echo $SERVICE_URL
# Output: https://westbethel-operator-xxxxx-uc.a.run.app
```

### Configure Twilio Webhooks

**In Twilio Console** (https://console.twilio.com):

1. Go to **Phone Numbers** → **Manage** → **Active Numbers**
2. Click on **+1 (207) 220-3501**
3. Under **Voice Configuration**:
   - **A CALL COMES IN**: Webhook
   - **URL**: `https://westbethel-operator-xxxxx.run.app/voice/twilio/inbound`
   - **HTTP**: POST
4. Under **Call Status Changes**:
   - **URL**: `https://westbethel-operator-xxxxx.run.app/voice/twilio/status`
   - **HTTP**: POST
5. **Save**

---

## Monitoring & Operations

### View Logs
```bash
# Stream logs
gcloud run services logs tail westbethel-operator --region us-central1

# View in Cloud Console
open "https://console.cloud.google.com/run/detail/us-central1/westbethel-operator/logs"
```

### Health Checks
```bash
SERVICE_URL=$(gcloud run services describe westbethel-operator --region us-central1 --format 'value(status.url)')

# Main health
curl $SERVICE_URL/health

# Voice health
curl $SERVICE_URL/voice/health

# Active sessions
curl $SERVICE_URL/voice/sessions
```

### Metrics & Monitoring
```bash
# View metrics in Cloud Console
open "https://console.cloud.google.com/run/detail/us-central1/westbethel-operator/metrics"

# Set up alerts
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="High Error Rate" \
    --condition-display-name="Error rate > 5%" \
    --condition-threshold-value=0.05
```

### Scaling Configuration
```bash
# Update scaling settings
gcloud run services update westbethel-operator \
    --region us-central1 \
    --min-instances 2 \
    --max-instances 20 \
    --concurrency 100
```

---

## Cost Optimization

### Current Configuration Cost Estimates

**Cloud Run** (2 vCPU, 2 GiB, min 1 instance):
- Always-on instance: ~$50/month
- Per-request: $0.00002400 per request
- CPU time: $0.00002400 per vCPU-second
- Memory: $0.00000250 per GiB-second

**Expected monthly cost** (1000 calls, avg 3 min):
- Cloud Run: ~$60
- OpenAI Realtime: ~$900
- Twilio: ~$60
- Cloud Storage: ~$1
- **Total**: ~$1,021/month

### Cost Reduction Strategies

1. **Reduce minimum instances**:
   ```bash
   gcloud run services update westbethel-operator \
       --min-instances 0  # Scale to zero when idle
   ```
   Saves ~$50/month but adds cold start latency

2. **Lower resource allocation**:
   ```bash
   gcloud run services update westbethel-operator \
       --cpu 1 \
       --memory 1Gi
   ```
   Saves ~$25/month

3. **Use Cloud SQL shared-core instance**:
   - db-f1-micro: $7/month (instead of $25+)

4. **Optimize call duration**:
   - Set `MAX_CALL_DURATION_MINUTES=5`
   - Transfer complex issues to humans
   - Saves on OpenAI costs

---

## Troubleshooting

### Deployment Issues

**Build fails**:
```bash
# Check build logs
gcloud builds list --limit=5

# View specific build
gcloud builds log BUILD_ID
```

**Container won't start**:
```bash
# Check service logs
gcloud run services logs read westbethel-operator \
    --region us-central1 \
    --limit 50
```

**Secret access denied**:
```bash
# Verify permissions
gcloud secrets get-iam-policy openai-api-key

# Grant access
PROJECT_NUMBER=$(gcloud projects describe westbethel-operator --format='value(projectNumber)')
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud secrets add-iam-policy-binding openai-api-key \
    --member="serviceAccount:$COMPUTE_SA" \
    --role="roles/secretmanager.secretAccessor"
```

### Runtime Issues

**Realtime API connection fails**:
- Check OpenAI API key in secrets
- Verify network egress allowed
- Check logs for specific error

**Twilio webhooks fail**:
- Verify webhook URLs are correct
- Check service allows unauthenticated access
- Test with curl first

**High latency**:
- Increase CPU/memory allocation
- Check external API response times
- Review logs for slow operations

---

## Security Best Practices

### Implemented
- ✅ Non-root container user
- ✅ Secrets in Secret Manager (not environment variables)
- ✅ HTTPS-only (Cloud Run enforced)
- ✅ Request validation (Twilio signatures)
- ✅ Rate limiting
- ✅ Health checks

### Recommended
- [ ] Enable VPC egress controls
- [ ] Set up Cloud Armor (DDoS protection)
- [ ] Enable audit logging
- [ ] Regular security scans
- [ ] Implement authentication for admin endpoints

---

## Rollback Procedure

### Rollback to Previous Version
```bash
# List revisions
gcloud run revisions list --service westbethel-operator --region us-central1

# Rollback to specific revision
gcloud run services update-traffic westbethel-operator \
    --region us-central1 \
    --to-revisions REVISION_NAME=100
```

### Emergency Rollback
```bash
# Deploy previous image
gcloud run deploy westbethel-operator \
    --image gcr.io/westbethel-operator/hotel-operator-agent:previous-tag \
    --region us-central1
```

---

## Maintenance

### Update Dependencies
```bash
# Update requirements.txt
pip list --outdated

# Rebuild and deploy
./deploy/deploy.sh
```

### Database Migrations
```bash
# Connect to Cloud SQL
gcloud sql connect westbethel-db --user=operator

# Run migrations
# (Use your migration tool: Alembic, etc.)
```

### Backup & Recovery
```bash
# Cloud SQL automated backups are enabled
# Manual backup:
gcloud sql backups create --instance=westbethel-db

# Restore from backup:
gcloud sql backups restore BACKUP_ID --backup-instance=westbethel-db
```

---

## Next Steps

### After Deployment

1. **Test Endpoints**:
   ```bash
   curl $SERVICE_URL/health
   curl $SERVICE_URL/voice/health
   ```

2. **Configure Twilio**:
   - Set webhook URLs
   - Test with phone call

3. **Set Up Monitoring**:
   - Create alerting policies
   - Set up uptime checks
   - Configure notification channels

4. **Production Testing**:
   - Make test calls
   - Verify function calling
   - Check logs and metrics

5. **Documentation**:
   - Document runbooks
   - Create incident response plan
   - Train team on operations

---

## Support & Resources

### Documentation
- [Cloud Run Docs](https://cloud.google.com/run/docs)
- [Secret Manager Docs](https://cloud.google.com/secret-manager/docs)
- [Cloud Build Docs](https://cloud.google.com/build/docs)

### Monitoring
- Cloud Console: https://console.cloud.google.com
- Logs Explorer: https://console.cloud.google.com/logs
- Metrics: https://console.cloud.google.com/monitoring

### Cost Management
- Billing Dashboard: https://console.cloud.google.com/billing
- Cost Calculator: https://cloud.google.com/products/calculator

---

## Conclusion

Your West Bethel Motel Hotel Operator Agent is now ready for cloud deployment!

**What you have**:
- ✅ Production-ready Dockerfile
- ✅ Automated deployment scripts
- ✅ Cloud Build CI/CD pipeline
- ✅ Secret management
- ✅ Scalable infrastructure
- ✅ Monitoring and logging

**To deploy**:
```bash
./deploy/setup-gcp.sh    # One-time setup
./deploy/deploy.sh       # Deploy anytime
```

**Your service will be live at**:
`https://westbethel-operator-xxxxx.run.app`

Welcome to production! 🚀
