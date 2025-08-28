# Simplified Dockerfile for debugging Next.js build issues

# Stage 1: Python dependencies (minimal)
FROM python:3.12-slim AS python-deps

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Stage 2: Dashboard (debug version)
FROM node:20-alpine AS dashboard-build

WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy entire dashboard directory at once
COPY dashboard/ ./dashboard/
WORKDIR /app/dashboard

# Debug: Show what we have
RUN echo "=== Dashboard directory structure ===" && \
    find . -type f -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.json" | head -20

RUN echo "=== Checking lib directory ===" && \
    ls -la lib/ || echo "lib directory missing"

RUN echo "=== Checking tsconfig paths ===" && \
    cat tsconfig.json

# Install dependencies
RUN pnpm install --frozen-lockfile

# Try building with more verbose output
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm run build || (echo "Build failed, showing more debug info:" && \
    echo "=== node_modules/@types existence ===" && \
    ls -la node_modules/@types/ | head -10 && \
    echo "=== Final attempt with --verbose ===" && \
    pnpm run build --verbose)

# Stage 3: Production
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    BACKEND_PORT=8080 \
    DASHBOARD_PORT=3000

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    corepack enable

RUN groupadd --gid 1001 app && \
    useradd --uid 1001 --gid app --shell /bin/bash --create-home app

COPY --from=python-deps /opt/venv /opt/venv

WORKDIR /app
COPY --chown=app:app . .

# Try copying built dashboard
COPY --from=dashboard-build --chown=app:app /app/dashboard/.next/standalone ./dashboard/
COPY --from=dashboard-build --chown=app:app /app/dashboard/.next/static ./dashboard/.next/static/
COPY --from=dashboard-build --chown=app:app /app/dashboard/public ./dashboard/public/

RUN mkdir -p /app/data /app/logs && chown -R app:app /app/data /app/logs
COPY --chown=app:app start.sh /app/start.sh
RUN chmod +x /app/start.sh

USER app
EXPOSE $BACKEND_PORT $DASHBOARD_PORT

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:${BACKEND_PORT}/docs && \
        curl -f http://localhost:${DASHBOARD_PORT} || exit 1

CMD ["/app/start.sh"]