# Multi-stage build for Medusa Backend
# Stage 1: Builder
FROM python:3.12-slim AS builder

# Копируем готовый бинарник uv прямо из официального образа
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Оптимизации для сборки
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Если есть C-зависимости, компиляторы ставим здесь
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы манифеста зависимостей (чтобы не сбрасывать кэш при правке кода)
COPY pyproject.toml uv.lock* ./

# Синхронизируем зависимости в /app/.venv с сохранением кэша uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev || \
    uv sync --no-install-project --no-dev


# Stage 2: Runner
FROM python:3.12-slim AS runner

ARG APP_VERSION
ENV APP_VERSION=${APP_VERSION} \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    PATH="/app/.venv/bin:$PATH"

LABEL maintainer="shizamuru-dev" \
      description="Medusa Backend - BSU Schedule API" \
      version="${APP_VERSION:-2.0.0}"

WORKDIR /app

RUN groupadd --gid 1001 app && \
    useradd --uid 1001 --gid app --shell /usr/sbin/nologin --no-create-home app

RUN mkdir -p /app/data /app/logs && \
    chown -R app:app /app

# Копируем виртуальное окружение из builder
COPY --from=builder /app/.venv /app/.venv

# Копируем исходники приложения
COPY --chown=app:app . .

COPY --chown=app:app docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER app

EXPOSE ${PORT}

# Health check на встроенном urllib без лишнего curl
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:' + '${PORT}' + '/docs').getcode() == 200 else 1)"

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
