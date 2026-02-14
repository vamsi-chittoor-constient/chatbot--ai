# =============================================================================
# Production Dockerfile for Restaurant AI Chatbot
# =============================================================================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY requirements.txt requirements_vector.txt ./
# Install CPU-only torch first (avoids downloading 5GB+ of CUDA/NVIDIA packages)
RUN pip install --upgrade pip && \
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install -r requirements.txt && \
    pip install -r requirements_vector.txt

# Pre-download sentence-transformers model to avoid first-request delays
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" || true

# -----------------------------------------------------------------------------
# Production Stage
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS production

LABEL maintainer="restaurant-ai" \
      version="1.0.0" \
      description="Restaurant AI Chatbot - CrewAI + FastAPI"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /root/.cache /home/appuser/.cache
RUN chown -R appuser:appuser /home/appuser/.cache
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copy application code
COPY app/ ./app/
COPY frontend/ ./frontend/
COPY static/ ./static/
COPY db/ ./db/
COPY requirements.txt .

RUN mkdir -p /app/logs /app/data/chromadb && chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--limit-concurrency", "100", \
     "--timeout-keep-alive", "120"]
