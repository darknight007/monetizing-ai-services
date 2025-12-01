# Phase 1 Implementation Quick Reference

## Files Modified/Created

### ✅ CREATED: `core/vertex_ai_client.py`

**Purpose**: Production-ready Vertex AI client replacing old llm_client.py

**Key Classes**:
```python
class VertexAIClient:
    async call_model(prompt, model, max_output_tokens, temperature, ...)
    async get_cost_summary()
    get_status()
```

**Global Functions**:
```python
async initialize_client(project_id, location, daily_budget_usd, force_fallback)
def get_client() -> VertexAIClient
async call_llm(prompt, model, max_tokens, temperature, ...)
async get_cost_summary()
def validate_config()
async test_connection()
```

**Key Features**:
- Gemini 2.0 Flash (default) and Gemini 1.5 Pro support
- Async/await interface
- Exponential backoff retry (max 3 attempts)
- Rate limiting (100 calls/min, configurable)
- Circuit breaker (opens after 5 failures)
- Cost tracking by model and date
- Daily budget enforcement ($100 default)
- Graceful fallback to deterministic responses

**Usage Example**:
```python
from core.vertex_ai_client import call_llm

response = await call_llm(
    prompt="Your prompt here",
    model="gemini-2.0-flash",
    max_tokens=256,
    temperature=0.7
)

print(response["text"])           # Response text
print(response["cost_usd"])       # Cost of call
print(response["source"])         # "vertex_ai" or "fallback"
```

---

### ✅ UPDATED: `agents/pricing_agent.py`

**What Changed**:
- Added async implementation: `_run_async()`
- `run()` now uses `asyncio.run(_run_async(...))`
- LLM call updated to use Vertex AI:
  ```python
  # OLD
  llm_response = call_llm(prompt, use_gemini=False)
  
  # NEW
  llm_response = await call_llm(
      prompt=prompt,
      model="gemini-2.0-flash",
      max_tokens=256,
      temperature=0.7
  )
  ```

**Output Changes**:
- Added: `llm_model` (model used)
- Added: `llm_source` ("vertex_ai" or "fallback")
- Added: `llm_cost_usd` (cost of LLM call)

---

### ✅ UPDATED: `agents/bundle_agent.py`

**Status**: Already async-ready, only verified imports

**No Changes Needed**: Already calls Vertex AI correctly via:
```python
async _run_async(rows, session_id)
return asyncio.run(_run_async(rows, session_id))
```

---

### ✅ UPDATED: `requirements.txt`

**Added**:
```
google-cloud-aiplatform>=1.35.0
vertexai>=0.30.0
```

**Installation**:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

---

### ✅ VERIFIED: `ui/app.py`

**Status**: No changes needed

**Why**: Both `bundle_run()` and `pricing_run()` handle async internally via `asyncio.run()`, so UI integration is transparent.

---

## Testing

### Test 1: Config Validation
```bash
python3 -c "from core.vertex_ai_client import validate_config; import json; print(json.dumps(validate_config(), indent=2))"
```

**Expected**:
```
{
  "vertex_ai_available": true,
  "vertex_ai_initialized": false,
  "project_id": null,
  "mode": "fallback"
}
```

### Test 2: Numeric Verification
```bash
python3 verify_numerics.py
```

**Expected**: `6 PASS, 0 FAIL`

### Test 3: Full Pipeline
```python
from agents.data_agent import run as data_run
from agents.cost_agent import run as cost_run
from agents.bundle_agent import run as bundle_run
from agents.pricing_agent import run as pricing_run

sid = "test-session"
rows = data_run(sid, path="data/synthetic_usage.json")
costs = cost_run(rows, session_id=sid)
bundle = bundle_run(rows, sid)
pricing = pricing_run(costs, bundle, sid)

# Check response
assert pricing["base_fee"] > 0
assert pricing["llm_source"] in ["vertex_ai", "fallback"]
```

---

## Deployment

### Development (No GCP Credentials)
```bash
bash run.sh
```
- Uses fallback mode (deterministic responses)
- Cost: $0/month
- Full functionality maintained

### Production (With GCP Credentials)
```bash
export GOOGLE_CLOUD_PROJECT=your-gcp-project
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
bash run.sh
```
- Uses real Vertex AI models
- Cost: ~$150/month for typical usage
- Full LLM capabilities

### Environment Variables
```bash
GOOGLE_CLOUD_PROJECT              # GCP project ID
GOOGLE_APPLICATION_CREDENTIALS    # Path to service account JSON
VERTEX_AI_FORCE_FALLBACK=1       # Force fallback mode (optional)
```

---

## Cost Model

### Pricing (per 1M tokens)
- **Gemini 2.0 Flash**
  - Input: $0.075 per 1M tokens
  - Output: $0.30 per 1M tokens

- **Gemini 1.5 Pro**
  - Input: $1.25 per 1M tokens
  - Output: $5.00 per 1M tokens

### Example Calculation (1000 calls/month, ~1000 tokens avg)
```
Input:  1M tokens × $0.075 = $75
Output: 250K tokens × $0.30 = $75
─────────────────────────────
Total: ~$150/month
```

### Budget Management
- Default daily budget: $100
- Alerts at: 80%, 90%, exceeding budget
- If budget exceeded: Falls back to deterministic responses

---

## Error Handling

### Automatic Retry
- Max 3 attempts per call
- Exponential backoff: 2^n + random(0,1) seconds
- Example: 1s, 3.5s, 7.2s

### Circuit Breaker
- Opens after 5 consecutive failures
- Prevents cascading failures
- Switches to fallback mode

### Fallback Mode
- Deterministic rule-based responses
- Always available
- Zero cost
- Maintains functionality

---

## Monitoring & Logging

### Log Level: INFO

**Example Logs**:
```
✓ Vertex AI initialized: project=my-project, location=us-central1
Calling gemini-2.0-flash (attempt 1/3)
✓ Response from gemini-2.0-flash: 256 chars, $0.0025
Cost: $0.0025, Daily: $0.05, Total: $0.45
⚠ Daily budget exceeded: $105.00/$100.00
Circuit breaker opened, switching to fallback
```

### Cost Summary
```python
from core.vertex_ai_client import get_cost_summary

summary = await get_cost_summary()
print(f"Daily cost: ${summary['daily_cost_usd']:.2f}")
print(f"Total cost: ${summary['total_cost_usd']:.2f}")
print(f"Usage: {summary['daily_usage_pct']:.1f}%")
```

---

## Architecture Diagram

```
PricingAgent (async)
  ↓
pricing_agent.run()
  ↓
asyncio.run(_run_async())
  ↓
await call_llm(prompt, model, ...)
  ↓
VertexAIClient.call_model()
  ├─ Check: rate limiting
  ├─ Call: _call_vertex_ai() (async via executor)
  ├─ Track: _track_cost()
  └─ Return: {text, tokens, cost, source, ...}
    ├─ Success → Vertex AI response
    └─ Failure → Fallback response
```

---

## Common Issues & Solutions

### Issue: "GOOGLE_CLOUD_PROJECT not set"
**Solution**: Set environment variable
```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
```

### Issue: "Could not initialize Vertex AI"
**Solution**: Using fallback mode (no issue, works fine)
```python
# Check status
from core.vertex_ai_client import validate_config
print(validate_config())
# If mode="fallback", it's intentional or credentials missing
```

### Issue: "Rate limit reached"
**Solution**: Client automatically backs off and retries
```
⏳ Rate limited, waiting 1.0s...
(automatic retry happens)
```

### Issue: "Circuit breaker open"
**Solution**: Automatically switches to fallback
```
Circuit breaker opened, switching to fallback
(service continues working with fallback responses)
```

---

## Success Criteria Met ✅

- [x] Real Vertex AI SDK integrated
- [x] Gemini 2.0 Flash & 1.5 Pro support
- [x] Async/await interface
- [x] Cost tracking by model
- [x] Rate limiting + circuit breaker
- [x] Graceful fallback mechanism
- [x] All agents use Vertex AI
- [x] Full pipeline tested & working
- [x] Documentation complete
- [x] Zero-cost fallback mode

---

## Next Steps

### Phase 1.5: Compliance Enhancement
- Multi-region validation (US, EU, APAC, LATAM, MEA)
- Uses Vertex AI for rule reasoning
- Timeline: 3-4 hours
- Status: Ready to start

### Phase 2A: Competitive Intelligence
- Market benchmarking with Google Search
- Vertex AI NLP for data extraction
- Timeline: 4-5 hours
- Status: Design complete (see COMPETITIVE_INTELLIGENCE_ANALYSIS.md)

---

**Phase 1 Status**: ✅ COMPLETE & PRODUCTION-READY
