# Multi-stage Docker build for Medusa Backend + Dashboard
# Stage 1: Build Python dependencies
FROM python:3.12-slim AS python-builder

LABEL authors="shizamuru-dev"
LABEL description="Medusa Backend + Dashboard - BSU Schedule API with UI"

# Set environment variables for build
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Stage 2: Build Next.js Dashboard
FROM node:18-alpine AS dashboard-builder

WORKDIR /app

# Install latest pnpm
RUN npm install -g pnpm@latest

# Copy dashboard source first
COPY dashboard/ ./

# Install dependencies
RUN pnpm i --frozen-lockfile

# Build the application
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm run build

# Stage 3: Production image
FROM python:3.12-slim AS production

LABEL authors="shizamuru-dev"
LABEL description="Medusa Backend + Dashboard - BSU Schedule API with UI"
LABEL version="1.0.0"

# Set production environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/opt/venv/bin:$PATH"
ENV PORT=8080
ENV DASHBOARD_PORT=3000

# Install runtime dependencies (including Node.js)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    nodejs \
    npm \
    supervisor \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge -y --auto-remove

# Install pnpm globally
RUN npm install -g pnpm

# Copy Python virtual environment from builder stage
COPY --from=python-builder /opt/venv /opt/venv

# Create non-root user for security
RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --shell /bin/bash --create-home app

# Set working directory
WORKDIR /app

# Copy backend application code with proper ownership
COPY --chown=app:app . .

# Copy dashboard build from builder stage
COPY --from=dashboard-builder --chown=app:app /app/.next/standalone ./dashboard/
COPY --from=dashboard-builder --chown=app:app /app/.next/static ./dashboard/.next/static
COPY --from=dashboard-builder --chown=app:app /app/public ./dashboard/public

# Create data directory with proper permissions
RUN mkdir -p /app/data && chown -R app:app /app/data

# Create supervisor configuration
COPY --chown=app:app <<EOF /etc/supervisor/conf.d/supervisord.conf
[supervisord]
nodaemon=true
user=root

[program:backend]
command=python /app/main.py
directory=/app
user=app
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0

[program:dashboard]
command=node /app/dashboard/server.js
directory=/app/dashboard
user=app
environment=NODE_ENV=production,NEXT_TELEMETRY_DISABLED=1,PORT=3000,HOSTNAME=0.0.0.0,API_BASE_URL=http://localhost:8080
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
EOF

# Expose ports
EXPOSE $PORT $DASHBOARD_PORT

# Health check for both services
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:$PORT/docs && curl -f http://localhost:$DASHBOARD_PORT || exit 1

# Run both services using supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]