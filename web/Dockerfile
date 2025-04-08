# --- Builder Stage (Node.js for React build) ---
FROM node:22-slim AS builder

WORKDIR /app/ui

# Copy package files and install dependencies
COPY ui/package.json ui/package-lock.json* ./
# Use ci for potentially faster and more reliable installs in CI/CD
RUN npm ci

# Copy the rest of the UI source code
COPY ui/. .

# Build the React app
RUN npm run build

# --- Final Stage (Python) ---
FROM python:3.12-slim AS base

# Install system dependencies for psycopg2
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
        libpq-dev \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python application code (excluding the ui source potentially)
# Copy everything EXCEPT the ui source directory, as we'll copy the build from the builder stage
COPY . .

# Copy the built React app from the builder stage
# This will place the built files into /app/ui/build in the final image
COPY --from=builder /app/ui/dist ./ui/dist

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default to development mode, can be overridden in compose
ENV FLASK_ENV=development \
    FLASK_DEBUG=1

# Expose port
EXPOSE 8888

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8888", "--workers", "1", "server:server"]
    