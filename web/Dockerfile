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

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default to development mode, can be overridden in compose
ENV FLASK_ENV=development \
    FLASK_DEBUG=1

# Expose port
EXPOSE 8888

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8888", "--workers", "1", "server:server"]