FROM python:slim-bookworm

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Expose the port (using ARG to make it dynamic)
ARG PORT=8888
ENV PORT=$PORT
EXPOSE ${PORT}

# Run using Gunicorn
CMD gunicorn --bind "0.0.0.0:${PORT}" --workers 1 "api:server" --log-level debug