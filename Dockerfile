# Use Python 3.10 slim image as base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install build dependencies, curl for healthcheck, and uv
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY splunk_mcp.py ./
COPY README.md ./
COPY .env.example ./

# Install dependencies using uv
RUN uv pip install --system poetry && \
    uv pip install --system -e .

# Create directory for environment file
RUN mkdir -p /app/config

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV SPLUNK_HOST=
ENV SPLUNK_PORT=8089
ENV SPLUNK_USERNAME=
ENV SPLUNK_PASSWORD=
ENV SPLUNK_SCHEME=https
ENV FASTMCP_LOG_LEVEL=INFO
ENV FASTMCP_PORT=8001
ENV DEBUG=false
ENV MODE=sse

# Expose the FastAPI port
EXPOSE 8001

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${FASTMCP_PORT}/health || exit 1

# Default to SSE mode
CMD ["python", "splunk_mcp.py", "sse"] 