# Combined Dockerfile for Mock Interview Hub
# Serves both FastAPI backend and React frontend in a single container

# =============================================================================
# Stage 1: Build Frontend
# =============================================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copy package files
COPY frontend/package.json frontend/package-lock.json ./

# Install dependencies
RUN npm ci

# Copy frontend source code
COPY frontend/ ./

# Build the application
RUN npm run build

# =============================================================================
# Stage 2: Final Combined Image
# =============================================================================
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    nodejs \
    npm \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install uv for Python dependency management
RUN pip install uv

# Set working directory for backend
WORKDIR /app/backend

# Copy backend dependency files
COPY backend/pyproject.toml backend/uv.lock ./

# Sync backend dependencies
RUN uv sync --frozen --no-dev

# Copy backend application code
COPY backend/app/ ./app/

# Copy frontend built assets to nginx html directory
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.combined.conf /etc/nginx/conf.d/default.conf

# Remove default nginx site configuration
RUN rm -f /etc/nginx/sites-enabled/default

# Copy supervisord configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose port 80
EXPOSE 80

# Start supervisord which manages nginx and the backend
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
