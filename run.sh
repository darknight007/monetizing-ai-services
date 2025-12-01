#!/usr/bin/env bash
#
# Quick Start Script for Ask-Scrooge
# Starts tax mock service and Streamlit UI
#

set -e

echo "🚀 Starting Ask-Scrooge Monetization Engine..."
echo ""

# Set PYTHONPATH
export PYTHONPATH="$(pwd)"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo ""
echo "✅ Dependencies installed"
echo ""

# Create output directory
mkdir -p output

# Start tax mock service in background
echo "🏦 Starting Tax Mock API (port 9000)..."
nohup uvicorn tools.openapi_tax_mock:app --port 9000 --log-level info > /tmp/tax_mock.log 2>&1 &
TAX_PID=$!

# Wait for tax service to be ready
echo "⏳ Waiting for Tax API to initialize..."
sleep 2

# Check if tax service is running
if curl -s http://localhost:9000/health > /dev/null 2>&1; then
    echo "✅ Tax Mock API running (PID: $TAX_PID)"
else
    echo "⚠️  Warning: Tax Mock API may not be ready yet"
fi

echo ""


# Start Gradio UI
echo "🌐 Starting Gradio UI (port 7860)..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Access the UI at: http://localhost:7860"
echo "  Tax API docs at:  http://localhost:9000/docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Start Gradio (this will block)
python ui/app.py

# Cleanup on exit
trap "echo ''; echo '🛑 Shutting down services...'; kill $TAX_PID 2>/dev/null || true; echo '✅ Stopped'; exit 0" INT TERM
