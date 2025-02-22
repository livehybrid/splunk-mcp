# Use Python 3.10 slim image as base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY splunk_mcp.py ./
COPY README.md ./
COPY .env.example ./

# Configure poetry to not create virtual environment in container
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev

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

# Expose the FastMCP port
EXPOSE 3000

# Command to run the application
CMD ["poetry", "run", "python", "splunk_mcp.py"] 