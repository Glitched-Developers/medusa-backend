# Multi-stage build for Medusa Backend (FastAPI) + Dashboard (Next.js)
# Fixed version with proper file copying and module resolution
COPY . ./app
WORKDIR ./app
# Stage 1: Build Python dependencies
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
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Stage 2: Build Next.js Dashboard
FROM node:20-alpine AS dashboard-build

# Install pnpm
RUN wget -qO- https://get.pnpm.io/install.sh | ENV="$HOME/.bashrc" SHELL="$(which bash)" bash -

# Set working directory and copy package files first
WORKDIR ./app/dashboard

RUN pnpm install --frozen-lockfile

ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm i

# Stage 3: Production runtime
FROM python:3.12-slim

LABEL maintainer="shizamuru-dev" \
      description="Medusa Backend + Dashboard - BSU Schedule API with UI" \
      version="2.0.0"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    BACKEND_PORT=8080 \
    DASHBOARD_PORT=3000

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    corepack enable

# Create non-root user
RUN groupadd --gid 1001 app && \
    useradd --uid 1001 --gid app --shell /bin/bash --create-home app

# Copy Python virtual environment
COPY --from=python-deps /opt/venv /opt/venv

# Set working directory and copy backend
WORKDIR ./app
COPY --chown=app:app . .

# Create directories with proper permissions
RUN mkdir -p /app/data /app/logs && \
    chown -R app:app /app/data /app/logs

# Copy and set up startup script
COPY --chown=app:app start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Switch to non-root user
USER app

# Expose ports
EXPOSE $BACKEND_PORT $DASHBOARD_PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:${BACKEND_PORT}/docs && \
        curl -f http://localhost:${DASHBOARD_PORT} || exit 1

# Start both services
CMD ["/app/start.sh"]