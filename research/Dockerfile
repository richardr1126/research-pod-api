FROM python:3.12-slim

# Install system dependencies for psycopg2
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
        libpq-dev \
        postgresql-client \
        libgomp1 \
            && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install and setup Crawl4AI and Playwright
RUN pip install -U crawl4ai && \
    python -m playwright install --with-deps chromium && \
    crawl4ai-setup

# Copy application code
COPY . .

# Create volume mount point for Milvus Lite .db
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose health check port
EXPOSE 8081

# Run the consumer
CMD ["python", "consumer.py"]