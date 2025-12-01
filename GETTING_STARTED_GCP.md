# Getting Started with Real Google Cloud & Vertex AI

## Quick Start (5 minutes)

### 1. Prerequisites Check

```bash
# Make sure you have gcloud CLI installed
gcloud --version

# Make sure you're authenticated
gcloud auth list
```

If gcloud is not installed, get it here: https://cloud.google.com/sdk/docs/install

### 2. Run Automated Setup

```bash
bash setup-gcp.sh
```

This script will:
- ✅ Ask for your GCP project
- ✅ Enable Vertex AI APIs
- ✅ Create service account
- ✅ Generate credentials
- ✅ Create `.env.gcp` file

### 3. Load Credentials

```bash
source .env.gcp
```

### 4. Test Vertex AI Connection

```bash
python3 test_vertex_ai.py
```

Expected output:
```
╔════════════════════════════════════════════════════════════════════════════╗
║                   ASK-SCROOGE: VERTEX AI TEST SUITE                        ║
╚════════════════════════════════════════════════════════════════════════════╝

TEST 1: Configuration Validation
  Vertex AI SDK Available: True
  Vertex AI Initialized: True
  Project ID: your-project-id
  Mode: VERTEX_AI

TEST 2: Vertex AI LLM Call
  Response: 4
  Source: VERTEX_AI
  Cost: $0.000150

✅ ALL TESTS PASSED
```

### 5. Run the Pipeline

```bash
bash run.sh
```

The UI will now use **real Gemini 2.0 Flash** for:
- Pricing recommendations
- Bundle analysis
- LLM justifications

---

## What You Get

### Real Gemini Models
- **Gemini 2.0 Flash**: Fast, real-time responses (~100-500ms)
- **Gemini 1.5 Pro**: Complex reasoning, detailed analysis (~200-800ms)

### Production Features
- ✅ Automatic retry with exponential backoff
- ✅ Rate limiting (100 calls/min default)
- ✅ Circuit breaker pattern
- ✅ Cost tracking by model
- ✅ Daily budget enforcement ($100 default)
- ✅ Graceful fallback if quota exceeded

### Real Pricing Recommendations
Instead of rule-based:
```
Base Fee: $143.55

Justification: "Based on the analysis of median monthly cost 
of $4.79, with a 3x margin applied and bundle optimization, 
I recommend a hybrid pricing model with these components..."
```

You get AI-powered:
```
Base Fee: $156.23

Justification: "Given the cost structure and market positioning, 
I recommend a tiered approach. The median customer has workflows 
in three categories. For your segment, a $156 base fee covers 
infrastructure costs with reasonable margin while remaining 
competitive for enterprise customers..."

(Real Gemini justification from LLM)
```

---

## Estimated Costs

### For Testing
- **1-5 API calls**: ~$0.001-0.005
- **10 API calls**: ~$0.01
- **100 API calls**: ~$0.10
- **1000 API calls/month**: ~$150

### Cost Control
```bash
# Default daily budget: $100
# To change:
export VERTEX_AI_DAILY_BUDGET_USD="500"

# Monitor costs:
python3 << 'EOF'
import asyncio
from core.vertex_ai_client import get_cost_summary
summary = asyncio.run(get_cost_summary())
print(f"Today's cost: ${summary['daily_cost_usd']:.2f}")
EOF
```

---

## Detailed Setup (if automated script doesn't work)

See: `GCP_SETUP_GUIDE.md` for step-by-step manual instructions

---

## Verify Real Vertex AI is Working

Check that the system is using real Gemini (not fallback):

```bash
source .env.gcp
python3 << 'EOF'
import asyncio
from core.vertex_ai_client import call_llm

async def test():
    response = await call_llm(
        prompt="What is 2+2?",
        model="gemini-2.0-flash"
    )
    print(f"Source: {response['source']}")  # Should be "vertex_ai"
    print(f"Model: {response['model']}")
    print(f"Text: {response['text']}")

asyncio.run(test())
EOF
```

If source is `"vertex_ai"` - you're using real Gemini! ✅

If source is `"fallback"` - credentials not found, still works fine

---

## Switch Between Modes

### Use Real Vertex AI
```bash
source .env.gcp
bash run.sh
```

### Use Fallback (no GCP needed)
```bash
unset GOOGLE_APPLICATION_CREDENTIALS
unset GOOGLE_CLOUD_PROJECT
bash run.sh
```

---

## Troubleshooting

### "gcloud command not found"
→ Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install

### "No projects found"
→ Create a GCP project at https://console.cloud.google.com/projectcreate

### "Permission denied"
→ Make sure service account has `roles/aiplatform.user` and `roles/aiplatform.admin`
→ See GCP_SETUP_GUIDE.md for role assignment

### "Rate limit exceeded"
→ System automatically backs off and retries
→ Adjust: `export VERTEX_AI_MAX_CALLS_PER_MINUTE="50"`

### "Budget exceeded"
→ System automatically falls back to deterministic responses
→ Check costs: `python3 test_vertex_ai.py`

---

## Next Steps

1. ✅ Set up credentials with `bash setup-gcp.sh`
2. ✅ Test with `python3 test_vertex_ai.py`
3. ✅ Run pipeline: `bash run.sh`
4. ⏳ Continue to Phase 1.5 (Compliance) for multi-region validation
5. ⏳ Add Phase 2A (Competitive Intelligence) for market benchmarking

---

## Documentation

- **GCP_SETUP_GUIDE.md**: Detailed Google Cloud setup instructions
- **PHASE_1_COMPLETION.md**: Phase 1 technical details
- **PHASE_1_QUICK_REFERENCE.md**: API and testing reference

---

**Status**: Ready to use real Gemini models! 🚀
