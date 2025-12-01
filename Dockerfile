# Multi-stage Dockerfile for Ask-Scrooge Monetization Engine
# Optimized for GCP Cloud Run with security best practices

# Stage 1: Base image with dependencies
FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies (minimal for Cloud Run)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first (leverage Docker cache)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# Stage 2: Production image (GCP Cloud Run optimized)
FROM python:3.11-slim AS production

# Metadata
LABEL maintainer="Ask-Scrooge Team"
LABEL version="1.0.0"
LABEL description="Global Dynamic Monetization Engine - GCP Cloud Run"

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/output && \
    chown -R appuser:appuser /app

WORKDIR /app

# Copy Python dependencies from base stage
COPY --from=base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=base /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser . .

# Set environment variables (GCP Cloud Run compatible)
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV USE_GEMINI=0
ENV PORT=8501
ENV TAX_API_PORT=9000

# Switch to non-root user
USER appuser

# Expose ports (Cloud Run uses PORT env var)
EXPOSE 8501 9000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:9000/health || exit 1

# Default command: run both services
# Note: Cloud Run requires single process, use supervisor in production
CMD ["sh", "-c", "uvicorn tools.openapi_tax_mock:app --host 0.0.0.0 --port 9000 --log-level info & streamlit run ui/app.py --server.port ${PORT:-8501} --server.address 0.0.0.0 --server.headless true --browser.serverAddress 0.0.0.0"]
