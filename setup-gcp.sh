#!/bin/bash
#
# Google Cloud Setup Script for Ask-Scrooge
# Configures real Vertex AI integration with Gemini models
#
# This script will:
# 1. Check for gcloud CLI
# 2. Ask for GCP project ID
# 3. Create/use service account
# 4. Set up authentication
# 5. Test Vertex AI connection
#

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                            ║"
echo "║     🚀 Ask-Scrooge: Google Cloud & Vertex AI Setup                        ║"
echo "║                                                                            ║"
echo "║     Configure real Gemini models for production                           ║"
echo "║                                                                            ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if gcloud is installed
echo "📋 Checking for Google Cloud SDK..."
if ! command -v gcloud &> /dev/null; then
    echo ""
    echo "❌ Google Cloud SDK not found!"
    echo ""
    echo "Please install gcloud CLI from:"
    echo "   https://cloud.google.com/sdk/docs/install"
    echo ""
    exit 1
fi

echo "✅ Google Cloud SDK found: $(gcloud --version | head -1)"
echo ""

# Check if already authenticated
echo "🔐 Checking Google Cloud authentication..."
if gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    CURRENT_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1)
    if [ -n "$CURRENT_ACCOUNT" ]; then
        echo "✅ Already authenticated as: $CURRENT_ACCOUNT"
        read -p "Use this account? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo ""
            echo "🔑 Please authenticate with Google Cloud..."
            gcloud auth login --no-launch-browser
        fi
    fi
else
    echo "🔑 Please authenticate with Google Cloud..."
    gcloud auth login --no-launch-browser
fi

echo ""
echo "📝 Google Cloud Project Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Get list of projects
PROJECTS=$(gcloud projects list --format="value(project_id)" 2>/dev/null || echo "")

if [ -z "$PROJECTS" ]; then
    echo "⚠️  No projects found in your account."
    echo ""
    echo "You need to create a GCP project first:"
    echo "   1. Go to https://console.cloud.google.com/projectcreate"
    echo "   2. Create a new project"
    echo "   3. Run this script again"
    echo ""
    exit 1
fi

echo "Available projects:"
echo ""
PROJECT_ARRAY=()
i=1
while IFS= read -r project; do
    echo "  $i) $project"
    PROJECT_ARRAY+=("$project")
    ((i++))
done <<< "$PROJECTS"

echo ""
read -p "Select project number (or enter project ID): " PROJECT_INPUT

if [[ "$PROJECT_INPUT" =~ ^[0-9]+$ ]]; then
    # User entered a number
    PROJECT_IDX=$((PROJECT_INPUT - 1))
    if [ $PROJECT_IDX -ge 0 ] && [ $PROJECT_IDX -lt ${#PROJECT_ARRAY[@]} ]; then
        GCP_PROJECT="${PROJECT_ARRAY[$PROJECT_IDX]}"
    else
        echo "❌ Invalid selection!"
        exit 1
    fi
else
    # User entered project ID directly
    GCP_PROJECT="$PROJECT_INPUT"
fi

echo ""
echo "Setting active project: $GCP_PROJECT"
gcloud config set project "$GCP_PROJECT"

echo ""
echo "📦 Enabling Required APIs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

REQUIRED_APIS=(
    "aiplatform.googleapis.com"
    "compute.googleapis.com"
    "cloudresourcemanager.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
    echo "Enabling $api..."
    gcloud services enable "$api" --quiet 2>/dev/null || true
done

echo "✅ APIs enabled"
echo ""

# Create or use service account
echo "🔑 Service Account Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

SERVICE_ACCOUNT="ask-scrooge-vertex-ai"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT}@${GCP_PROJECT}.iam.gserviceaccount.com"

# Check if service account exists
if gcloud iam service-accounts describe "$SERVICE_ACCOUNT_EMAIL" --project="$GCP_PROJECT" &> /dev/null; then
    echo "✅ Service account exists: $SERVICE_ACCOUNT_EMAIL"
else
    echo "Creating service account: $SERVICE_ACCOUNT"
    gcloud iam service-accounts create "$SERVICE_ACCOUNT" \
        --display-name="Ask-Scrooge Vertex AI Service Account" \
        --project="$GCP_PROJECT"
    echo "✅ Service account created"
fi

echo ""
echo "📋 Assigning IAM Roles"
echo ""

REQUIRED_ROLES=(
    "roles/aiplatform.user"
    "roles/aiplatform.admin"
)

for role in "${REQUIRED_ROLES[@]}"; do
    echo "Granting $role..."
    gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="$role" \
        --quiet 2>/dev/null || true
done

echo "✅ IAM roles assigned"
echo ""

# Create and download service account key
echo "🔐 Creating Service Account Key"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

KEY_FILE="$HOME/.config/gcp/ask-scrooge-key.json"
KEY_DIR="$(dirname "$KEY_FILE")"

mkdir -p "$KEY_DIR"

if [ -f "$KEY_FILE" ]; then
    echo "✅ Key file already exists: $KEY_FILE"
    read -p "Regenerate key? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gcloud iam service-accounts keys create "$KEY_FILE" \
            --iam-account="$SERVICE_ACCOUNT_EMAIL" \
            --project="$GCP_PROJECT"
        echo "✅ New key created"
    fi
else
    echo "Creating service account key..."
    gcloud iam service-accounts keys create "$KEY_FILE" \
        --iam-account="$SERVICE_ACCOUNT_EMAIL" \
        --project="$GCP_PROJECT"
    echo "✅ Key saved: $KEY_FILE"
fi

echo ""

# Set environment variables
echo "🔧 Setting up Environment Variables"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

ENV_FILE=".env.gcp"

cat > "$ENV_FILE" << EOF
# Google Cloud Configuration for Ask-Scrooge
# Generated: $(date)

export GOOGLE_CLOUD_PROJECT="$GCP_PROJECT"
export GOOGLE_APPLICATION_CREDENTIALS="$KEY_FILE"
export GCLOUD_PROJECT="$GCP_PROJECT"

# Vertex AI Configuration
export VERTEX_AI_LOCATION="us-central1"
export VERTEX_AI_MODEL_FLASH="gemini-2.0-flash"
export VERTEX_AI_MODEL_PRO="gemini-1.5-pro"

# Budget & Limits
export VERTEX_AI_DAILY_BUDGET_USD="100"
export VERTEX_AI_MAX_CALLS_PER_MINUTE="100"

# Feature Flags
export USE_VERTEX_AI="1"
export VERTEX_AI_FORCE_FALLBACK="0"
EOF

echo "✅ Environment file created: $ENV_FILE"
echo ""
echo "Configuration saved to: $ENV_FILE"
echo ""

# Display how to use
echo "📝 Next Steps"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Load the environment variables:"
echo ""
echo "   source $ENV_FILE"
echo ""
echo "2. Verify setup:"
echo ""
echo "   python3 -c 'from core.vertex_ai_client import validate_config; import json; print(json.dumps(validate_config(), indent=2))'"
echo ""
echo "3. Test Vertex AI connection:"
echo ""
echo "   python3 << 'TESTEOF'"
echo "   import asyncio"
echo "   from core.vertex_ai_client import test_connection"
echo "   result = asyncio.run(test_connection())"
echo "   TESTEOF"
echo ""
echo "4. Run the pipeline:"
echo ""
echo "   bash run.sh"
echo ""
echo ""
echo "✅ Setup Complete!"
echo ""
echo "Your Vertex AI credentials:"
echo "  Project: $GCP_PROJECT"
echo "  Service Account: $SERVICE_ACCOUNT_EMAIL"
echo "  Key File: $KEY_FILE"
echo ""
echo "⚠️  Keep the key file secure! Never commit it to version control."
echo ""

# Optional: load environment now
read -p "Load environment variables now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    source "$ENV_FILE"
    echo "✅ Environment variables loaded"
    echo ""
    echo "Current configuration:"
    echo "  GOOGLE_CLOUD_PROJECT: $GOOGLE_CLOUD_PROJECT"
    echo "  GOOGLE_APPLICATION_CREDENTIALS: $GOOGLE_APPLICATION_CREDENTIALS"
    echo ""
fi
