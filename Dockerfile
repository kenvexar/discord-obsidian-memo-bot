# Multi-stage build for production optimization
FROM python:3.13.7-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set environment variables
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Create working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Production stage
FROM python:3.13.7-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=app:app /app/.venv /app/.venv

# Copy application code
COPY --chown=app:app src/ ./src/
COPY --chown=app:app README.md ./

# Create logs directory
RUN mkdir -p logs && chown app:app logs

# Switch to non-root user
USER app

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "src/main.py"]
