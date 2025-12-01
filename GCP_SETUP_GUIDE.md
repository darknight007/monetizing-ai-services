# Google Cloud Setup for Ask-Scrooge

This guide walks through setting up real Google Cloud Vertex AI for the Ask-Scrooge monetization engine.

## Prerequisites

1. **Google Cloud Account**
   - Go to https://console.cloud.google.com
   - Create a new GCP project (if you don't have one)
   - Note your Project ID

2. **Google Cloud SDK**
   - Install gcloud CLI: https://cloud.google.com/sdk/docs/install
   - Verify: `gcloud --version`

## Quick Setup (Automated)

```bash
bash setup-gcp.sh
```

This script will:
- ✅ Authenticate with Google Cloud
- ✅ Select your GCP project
- ✅ Enable required APIs
- ✅ Create service account
- ✅ Generate credentials
- ✅ Set environment variables

Then load the environment:
```bash
source .env.gcp
```

## Manual Setup (Step-by-Step)

### Step 1: Authenticate with Google Cloud

```bash
gcloud auth login --no-launch-browser
```

This opens a browser for authentication. Copy the auth code back to the terminal.

### Step 2: Set Project

```bash
gcloud config set project YOUR-PROJECT-ID
```

Replace `YOUR-PROJECT-ID` with your actual GCP project ID.

### Step 3: Enable Required APIs

```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
```

### Step 4: Create Service Account

```bash
gcloud iam service-accounts create ask-scrooge-vertex-ai \
  --display-name="Ask-Scrooge Vertex AI Service Account"
```

### Step 5: Grant IAM Roles

```bash
PROJECT_ID=$(gcloud config get-value project)
SERVICE_ACCOUNT_EMAIL="ask-scrooge-vertex-ai@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/aiplatform.admin"
```

### Step 6: Create and Download Key

```bash
mkdir -p ~/.config/gcp

gcloud iam service-accounts keys create ~/.config/gcp/ask-scrooge-key.json \
  --iam-account="$SERVICE_ACCOUNT_EMAIL"
```

### Step 7: Set Environment Variables

```bash
export GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project)
export GOOGLE_APPLICATION_CREDENTIALS=~/.config/gcp/ask-scrooge-key.json
export VERTEX_AI_LOCATION="us-central1"
```

Or create `.env.gcp`:
```bash
cat > .env.gcp << 'EOF'
export GOOGLE_CLOUD_PROJECT="YOUR-PROJECT-ID"
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcp/ask-scrooge-key.json"
export VERTEX_AI_LOCATION="us-central1"
EOF

source .env.gcp
```

## Verify Setup

### Check Configuration

```bash
python3 << 'EOF'
from core.vertex_ai_client import validate_config
import json

config = validate_config()
print(json.dumps(config, indent=2))
EOF
```

Expected output:
```json
{
  "vertex_ai_available": true,
  "vertex_ai_initialized": true,
  "project_id": "your-project-id",
  "location": "us-central1",
  "circuit_open": false,
  "failure_count": 0,
  "mode": "vertex_ai"
}
```

### Test Connection

```bash
python3 << 'EOF'
import asyncio
from core.vertex_ai_client import test_connection

result = asyncio.run(test_connection())
print(f"Connection test: {'✅ PASSED' if result else '❌ FAILED'}")
EOF
```

## Run the Pipeline with Real Gemini

```bash
# Load credentials
source .env.gcp

# Run with real Vertex AI
bash run.sh
```

The UI will now use real Gemini models for:
- Bundle recommendations
- Pricing justifications
- Compliance analysis

## Cost Management

### Daily Budget

The system enforces a daily budget of $100 USD by default. To change:

```bash
export VERTEX_AI_DAILY_BUDGET_USD="500"
```

### Monitor Costs

Check current costs:

```bash
python3 << 'EOF'
import asyncio
from core.vertex_ai_client import get_cost_summary

summary = asyncio.run(get_cost_summary())
print(f"Daily cost: ${summary['daily_cost_usd']:.2f}")
print(f"Total cost: ${summary['total_cost_usd']:.2f}")
print(f"Usage: {summary['daily_usage_pct']:.1f}%")
EOF
```

## Available Models

### Gemini 2.0 Flash (Default)
- **Use case**: Fast, real-time responses
- **Cost**: $0.075 input / $0.30 output (per 1M tokens)
- **Latency**: 100-500ms
- **Best for**: Pricing recommendations, bundle analysis

### Gemini 1.5 Pro
- **Use case**: Complex reasoning, detailed analysis
- **Cost**: $1.25 input / $5.00 output (per 1M tokens)
- **Latency**: 200-800ms
- **Best for**: Compliance analysis, complex multi-region logic

## Troubleshooting

### Issue: "GOOGLE_APPLICATION_CREDENTIALS not found"

**Solution**: Make sure the key file path is correct
```bash
export GOOGLE_APPLICATION_CREDENTIALS=~/.config/gcp/ask-scrooge-key.json
ls -la $GOOGLE_APPLICATION_CREDENTIALS  # Verify file exists
```

### Issue: "Could not initialize Vertex AI"

**Solution**: Check if credentials are valid
```bash
gcloud auth application-default print-access-token
# If this fails, re-authenticate:
gcloud auth login
```

### Issue: "Permission denied" or "403 Forbidden"

**Solution**: Make sure service account has correct roles
```bash
gcloud projects get-iam-policy $(gcloud config get-value project) \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:*"
```

The service account should have:
- `roles/aiplatform.user`
- `roles/aiplatform.admin`

### Issue: "Rate limit exceeded"

**Solution**: The system automatically backs off. Check if you're within limits:
- Default: 100 calls/minute
- Adjust: `export VERTEX_AI_MAX_CALLS_PER_MINUTE="50"`

### Issue: "Budget exceeded"

**Solution**: System falls back to deterministic responses when budget is exceeded
- Check your daily cost
- Increase budget: `export VERTEX_AI_DAILY_BUDGET_USD="200"`
- Or check for unexpected usage patterns

## Security Best Practices

1. **Never commit credentials to git**
   ```bash
   echo ".env.gcp" >> .gitignore
   echo "~/.config/gcp/" >> .gitignore
   ```

2. **Rotate keys regularly**
   ```bash
   # Delete old key
   gcloud iam service-accounts keys list --iam-account=$SERVICE_ACCOUNT_EMAIL
   gcloud iam service-accounts keys delete KEY_ID --iam-account=$SERVICE_ACCOUNT_EMAIL
   
   # Create new key
   gcloud iam service-accounts keys create ~/.config/gcp/ask-scrooge-key.json \
     --iam-account=$SERVICE_ACCOUNT_EMAIL
   ```

3. **Use least privilege**
   - Service account has only roles needed for Vertex AI
   - Not added to Owner or Editor roles

4. **Monitor API usage**
   - https://console.cloud.google.com/apis/dashboard
   - Check quota usage
   - Set up billing alerts

## Next Steps

1. **Run the pipeline** with real Gemini models:
   ```bash
   source .env.gcp
   bash run.sh
   ```

2. **Test pricing recommendations** with real LLM justifications

3. **Monitor costs** and adjust budget as needed

4. **Configure for compliance** (Phase 1.5) with multi-region validation

## Support

For issues with:
- **Google Cloud**: https://cloud.google.com/support
- **Vertex AI**: https://cloud.google.com/vertex-ai/docs
- **Ask-Scrooge**: Check PHASE_1_QUICK_REFERENCE.md

---

**Status**: Ready to use real Gemini models! 🚀
