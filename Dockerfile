FROM python:slim

WORKDIR /app

# Install dependencies
COPY research/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY research/ ./research/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Expose the port (using a default value)
EXPOSE 8080

# Run using Gunicorn
CMD gunicorn --bind "0.0.0.0:8080" --workers 1 "research.server:server" --log-level debug 