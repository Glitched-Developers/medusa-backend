# Single-stage build for Medusa Backend (FastAPI)
FROM python:3.12-slim AS production

# Accept build-time version argument
ARG APP_VERSION
ENV APP_VERSION=${APP_VERSION}

LABEL maintainer="shizamuru-dev" \
      description="Medusa Backend - BSU Schedule API" \
      version="2.0.0"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8080

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/libs/apt/lists/*

# Create non-root user
RUN groupadd --gid 1001 app && \
    useradd --uid 1001 --gid app --shell /bin/bash --create-home app

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY --chown=app:app . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/data /app/logs && \
    chown -R app:app /app/data /app/logs

# Expose port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:${PORT}/docs || exit 1

# Start service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]