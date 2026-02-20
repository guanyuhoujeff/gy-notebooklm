# Use official Python runtime as a parent image
FROM python:3.12-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

# Install system dependencies required for Playwright and general usage
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set work directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install python dependencies
RUN uv pip install -r requirements.txt

# Install Playwright browsers and dependencies
# We only need chromium for notebooklm-py
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy the server code
COPY mcp_server.py .

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run the application
# Host 0.0.0.0 is crucial for Docker networking
CMD ["fastmcp", "run", "mcp_server.py", "--transport", "sse", "--port", "8000", "--host", "0.0.0.0"]
