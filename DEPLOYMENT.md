# Ask-Scrooge Deployment Guide

## Quick Start Options

### Option 1: Local Development (Fastest)

```bash
# Clone and navigate to project
cd /Users/outlieralpha/CascadeProjects/ask-scrooge

# Run the quick start script
./run.sh
```

Access:
- **Streamlit UI**: http://localhost:8501
- **Tax API Docs**: http://localhost:9000/docs

### Option 2: Docker Compose (Recommended for Testing)

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 3: Docker (Manual)

```bash
# Build image
docker build -t ask-scrooge:latest .

# Run container
docker run -p 8501:8501 -p 9000:9000 \
  -e USE_GEMINI=0 \
  -v $(pwd)/output:/app/output \
  ask-scrooge:latest
```

## GCP Cloud Run Deployment

### Prerequisites

1. GCP Project with billing enabled
2. `gcloud` CLI installed and authenticated
3. Container Registry or Artifact Registry enabled

### Step 1: Setup Environment

```bash
# Set GCP project
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"

gcloud config set project $GCP_PROJECT_ID
```

### Step 2: Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com \
  logging.googleapis.com
```

### Step 3: Build and Push Image

```bash
# Build with Cloud Build
gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/ask-scrooge

# Or build locally and push
docker build -t gcr.io/$GCP_PROJECT_ID/ask-scrooge .
docker push gcr.io/$GCP_PROJECT_ID/ask-scrooge
```

### Step 4: Deploy to Cloud Run

```bash
gcloud run deploy ask-scrooge \
  --image gcr.io/$GCP_PROJECT_ID/ask-scrooge \
  --platform managed \
  --region $GCP_REGION \
  --allow-unauthenticated \
  --set-env-vars USE_GEMINI=0,ENABLE_GCP_LOGGING=1 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0
```

### Step 5: Get Service URL

```bash
gcloud run services describe ask-scrooge \
  --platform managed \
  --region $GCP_REGION \
  --format 'value(status.url)'
```

## GitHub Actions CI/CD Setup

### Prerequisites

1. GitHub repository
2. GCP Service Account with permissions:
   - Cloud Run Admin
   - Storage Admin
   - Service Account User

### Step 1: Create Service Account

```bash
# Create service account
gcloud iam service-accounts create github-actions \
  --display-name "GitHub Actions CI/CD"

# Grant permissions
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:github-actions@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:github-actions@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:github-actions@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Create and download key
gcloud iam service-accounts keys create ~/gcp-key.json \
  --iam-account github-actions@$GCP_PROJECT_ID.iam.gserviceaccount.com
```

### Step 2: Configure GitHub Secrets

Add these secrets to your GitHub repository (Settings > Secrets and variables > Actions):

- `GCP_PROJECT_ID`: Your GCP project ID
- `GCP_SA_KEY`: Contents of `~/gcp-key.json` (paste entire JSON)

### Step 3: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: Ask-Scrooge monetization engine"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ask-scrooge.git
git push -u origin main
```

The CI/CD pipeline will automatically:
1. Run linting and code quality checks
2. Execute unit and integration tests
3. Perform security scanning
4. Build and push Docker image
5. Deploy to Cloud Run (on main branch)

## Environment Configuration

### Local Development

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` with your configuration:
```bash
# Enable Gemini (optional)
USE_GEMINI=1
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Tax API
TAX_API_KEY=your-secure-key

# Logging
LOG_LEVEL=INFO
ENABLE_GCP_LOGGING=1
```

### Production (GCP Cloud Run)

Set environment variables in Cloud Run:

```bash
gcloud run services update ask-scrooge \
  --region $GCP_REGION \
  --set-env-vars \
    USE_GEMINI=1,\
    GOOGLE_CLOUD_PROJECT=$GCP_PROJECT_ID,\
    ENABLE_GCP_LOGGING=1,\
    LOG_LEVEL=INFO,\
    LLM_DAILY_BUDGET_USD=1000,\
    TAX_API_KEY=your-secure-production-key
```

## Testing

### Unit Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=core --cov=agents --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Smoke Test

```bash
# Run smoke test (no UI)
./scripts/smoke_run.sh
```

### Manual Testing

1. Start services: `./run.sh`
2. Open browser: http://localhost:8501
3. Click "Run Full Pipeline"
4. Verify all agents complete successfully
5. Download audit ledger and invoice

## Monitoring and Observability

### GCP Cloud Logging

View logs in GCP Console:

```bash
# Open logs explorer
open "https://console.cloud.google.com/logs/query?project=$GCP_PROJECT_ID"

# View specific service logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ask-scrooge" \
  --limit 50 \
  --format json
```

### Audit Trail

Audit ledger is written to `output/audit_ledger.jsonl`:

```bash
# View audit log
cat output/audit_ledger.jsonl | jq .

# Query specific session
cat output/audit_ledger.jsonl | jq 'select(.session=="YOUR_SESSION_ID")'

# Query specific agent
cat output/audit_ledger.jsonl | jq 'select(.agent=="PricingAgent")'
```

### Health Checks

```bash
# Check tax API health
curl http://localhost:9000/health

# Check service health (Cloud Run)
curl https://YOUR-SERVICE-URL.run.app/health
```

## Troubleshooting

### Issue: Port already in use

```bash
# Find and kill process on port 9000
lsof -ti:9000 | xargs kill -9

# Find and kill process on port 8501
lsof -ti:8501 | xargs kill -9
```

### Issue: Module not found

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=$(pwd)

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Tax API authentication fails

```bash
# Check API key is set
echo $TAX_API_KEY

# Set API key
export TAX_API_KEY=demo-key-12345

# Or update .env file
echo "TAX_API_KEY=demo-key-12345" >> .env
```

### Issue: GCP deployment fails

```bash
# Check Cloud Run logs
gcloud run services logs read ask-scrooge --limit=50

# Check build logs
gcloud builds list --limit=5

# Verify service account permissions
gcloud projects get-iam-policy $GCP_PROJECT_ID
```

## Security Best Practices

### SOC2 Compliance Checklist

- [ ] Rotate API keys regularly (90 days recommended)
- [ ] Enable GCP audit logging
- [ ] Implement least-privilege access control
- [ ] Encrypt data at rest and in transit
- [ ] Regular security scanning (automated in CI/CD)
- [ ] Maintain audit trail for all operations
- [ ] Regular backup of audit logs
- [ ] Incident response plan documented

### Secrets Management

**NEVER commit secrets to Git!**

Use:
- GCP Secret Manager for production
- Environment variables for development
- `.env` file (gitignored) for local testing

```bash
# Store secret in GCP Secret Manager
echo -n "your-secret-key" | gcloud secrets create tax-api-key --data-file=-

# Grant access to Cloud Run
gcloud secrets add-iam-policy-binding tax-api-key \
  --member="serviceAccount:github-actions@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Performance Optimization

### Scaling Configuration

```bash
# Update Cloud Run scaling
gcloud run services update ask-scrooge \
  --region $GCP_REGION \
  --min-instances 1 \
  --max-instances 100 \
  --cpu 2 \
  --memory 2Gi \
  --concurrency 80
```

### Budget Management

LLM costs are tracked automatically. Configure budget alerts:

```bash
# Set daily budget in environment
export LLM_DAILY_BUDGET_USD=100

# Monitor usage in logs
gcloud logging read "jsonPayload.message=~'Budget Alert'" --limit 10
```

## Backup and Disaster Recovery

### Backup Audit Logs

```bash
# Copy audit logs to GCS
gsutil cp output/audit_ledger.jsonl gs://your-backup-bucket/$(date +%Y%m%d)/
```

### Disaster Recovery Plan

1. **Code**: GitHub repository (main source of truth)
2. **Container Images**: GCR (automatic retention)
3. **Audit Logs**: GCS backup (automated)
4. **Configuration**: GCP Secret Manager

Recovery Time Objective (RTO): < 15 minutes
Recovery Point Objective (RPO): < 1 hour

## Support

For issues or questions:
1. Check README.md for architecture and assumptions
2. Review logs: `output/audit_ledger.jsonl`
3. Check GCP Cloud Logging
4. Review GitHub Actions logs
5. Contact: CTO team

---

**Last Updated**: December 1, 2025
**Version**: 1.0.0
