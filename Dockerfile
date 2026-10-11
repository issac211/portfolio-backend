# =============================================================================
# Build Stage: Extract pinned uv binary from Astral's official image
# =============================================================================
FROM ghcr.io/astral-sh/uv:0.11.28 AS uv_bin

# =============================================================================
# Runtime Stage: Production Python slim container
# =============================================================================
FROM python:3.14-slim-bookworm

# Metadata
LABEL maintainer="Portfolio Engineering Team"
LABEL description="Production and development container for FastAPI portfolio backend"

# Optimization & safety environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install runtime utilities (curl required for container healthcheck probes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy uv package manager binaries from the pinned official image
COPY --from=uv_bin /uv /uvx /bin/

# -----------------------------------------------------------------------------
# Dependency Layer Caching
# Copy ONLY dependency manifests to leverage Docker build cache
# -----------------------------------------------------------------------------
COPY pyproject.toml uv.lock ./

# Install project dependencies into /app/.venv without project source code
# --frozen: guarantees strict adherence to uv.lock without network mutations
# --no-install-project: avoids installing the root package before source files exist
# --no-dev: excludes test/lint runners (pytest, ruff) for minimal image footprint
RUN uv sync --frozen --no-install-project --no-dev

# Place the virtualenv on system PATH and configure source discovery
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src"

# -----------------------------------------------------------------------------
# Application Source Code Layer
# -----------------------------------------------------------------------------
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# -----------------------------------------------------------------------------
# Security & Permissions (Least Privilege Principle)
# -----------------------------------------------------------------------------
RUN useradd -m -u 10001 appuser && \
    mkdir -p /app/uploads && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Default production entrypoint (Overridden in docker-compose for dev hot-reloading)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
