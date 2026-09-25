# ============================================
# Turbo ElSayed - production image
# ============================================
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PORT=8501

WORKDIR /app

# ffmpeg is mandatory: every render shells out to it.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY requirements.txt* ./

# uv.lock is the source of truth; requirements.txt is the fallback.
RUN uv sync --frozen --no-dev || pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p storage output resource/songs resource/fonts tmp \
    && useradd --uid 10001 --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app

USER 10001:10001

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT}/ping" || exit 1

CMD ["sh", "-c", "uv run uvicorn app.asgi:app --host 0.0.0.0 --port ${PORT} --log-level warning"]
