#!/usr/bin/env bash
#
# Smoke Test Script
# Tests the entire pipeline without UI
#

set -e

echo "🧪 Running Ask-Scrooge Smoke Test..."
echo ""

# Set PYTHONPATH
export PYTHONPATH="$(pwd)"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start tax mock service
echo "🏦 Starting Tax Mock API..."
nohup uvicorn tools.openapi_tax_mock:app --port 9000 --log-level info > /tmp/tax_mock.log 2>&1 &
TAX_PID=$!

# Wait for service to be ready
echo "⏳ Waiting for API to initialize..."
sleep 2

# Check health
if curl -s http://localhost:9000/health > /dev/null 2>&1; then
    echo "✅ Tax Mock API is healthy"
else
    echo "❌ Tax Mock API failed to start"
    kill $TAX_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "▶️  Running pipeline test..."
echo ""

# Run pipeline programmatically
python3 - <<'PYTHON_SCRIPT'
import sys
import traceback
from core.session_service import InMemorySessionService
from agents.data_agent import run as data_run
from agents.cost_agent import run as cost_run
from agents.bundle_agent import run as bundle_run
from agents.pricing_agent import run as pricing_run
from agents.compliance_agent import run as compliance_run

try:
    print("🔧 Initializing session...")
    sess = InMemorySessionService()
    sid = sess.create_session()
    print(f"✅ Session created: {sid[:8]}...")
    print()
    
    print("📊 Running Data Agent...")
    rows = data_run(sid)
    print(f"✅ Aggregated {len(rows)} rows")
    print()
    
    print("💰 Running Cost Agent...")
    cost_rows = cost_run(rows, session_id=sid)
    print(f"✅ Calculated {len(cost_rows)} cost projections")
    print()
    
    print("📦 Running Bundle Agent...")
    bundle = bundle_run(rows, sid)
    print(f"✅ Proposed bundle: {bundle['bundle_name']}")
    print()
    
    print("💵 Running Pricing Agent...")
    rec = pricing_run(cost_rows, bundle, sid)
    print(f"✅ Pricing: ${rec['base_fee']}/month base + usage")
    print()
    
    print("🛡️  Running Compliance Agent...")
    comp = compliance_run(rec, "US", session_id=sid)
    print(f"✅ Compliance: {comp.get('compliance_status', 'UNKNOWN')}")
    print()
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📋 PIPELINE RESULTS")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print(f"Bundle: {bundle['bundle_name']}")
    print(f"Expected Uplift: {bundle['expected_uplift_pct']}%")
    print()
    print(f"Pricing Model: {rec['model']}")
    print(f"  Base Fee: ${rec['base_fee']}/month")
    print(f"  Per Workflow: ${rec['per_workflow']}")
    print(f"  Per 1K Tokens: ${rec['per_1k_tokens']}")
    print()
    print(f"Compliance: {comp.get('compliance_status')}")
    print(f"  Region: {comp.get('region')}")
    print(f"  VAT: {comp.get('vat', 0)}%")
    print(f"  Total with Tax: ${comp.get('total_with_tax', 0)}")
    print()
    print("✅ SMOKE TEST PASSED")
    sys.exit(0)
    
except Exception as e:
    print()
    print("❌ SMOKE TEST FAILED")
    print(f"Error: {str(e)}")
    print()
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

RESULT=$?

# Cleanup
echo ""
echo "🧹 Cleaning up..."
kill $TAX_PID 2>/dev/null || true

# Check results
echo ""
if [ $RESULT -eq 0 ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ All tests passed!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📁 Outputs:"
    echo "  - output/audit_ledger.jsonl"
    echo ""
    exit 0
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "❌ Tests failed"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Check logs:"
    echo "  - /tmp/tax_mock.log"
    echo ""
    exit 1
fi
