FROM python:3.11-slim

# Set metadata
LABEL maintainer="PHOENIX Radar AI Team"
LABEL description="Production-ready Docker image for PHOENIX Cognitive Photonic Radar System"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Set Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy requirements files
COPY photonic-radar-ai/requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Create runtime directories for shared state and logs
RUN mkdir -p runtime logs && \
    chmod 755 runtime logs

# Create non-root user for security (optional but recommended)
RUN groupadd -r phoenix && useradd -r -g phoenix phoenix && \
    chown -R phoenix:phoenix /app
USER phoenix

# Expose ports
# API Server (FastAPI/Flask): 5000 → 8000 (in docker-compose)
# Streamlit UI: 8501
EXPOSE 5000 8501

# Health check for API server
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Default command runs main.py
CMD ["python", "main.py"]
