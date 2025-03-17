FROM python:3.12-slim AS base

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
# gunicorn --bind 0.0.0.0:8080 --workers 1 server:server
# flask run --port 8888