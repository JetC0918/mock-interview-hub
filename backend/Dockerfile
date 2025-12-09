# Backend Dockerfile for FastAPI with uv
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files first (for better layer caching)
COPY pyproject.toml uv.lock ./

# Sync dependencies with uv
RUN uv sync --frozen --no-dev

# Copy application code
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Run the application with uvicorn via uv
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
