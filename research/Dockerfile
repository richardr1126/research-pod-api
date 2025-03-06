FROM python:slim

WORKDIR /app

#RUN PYMUPDF_SETUP_PY_LIMITED_API=0 pip install -U pymupdf4llm

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Expose the port (using a default value)
EXPOSE 8080

# Run using Gunicorn
CMD gunicorn --bind "0.0.0.0:8080" --workers 1 "server:server" --log-level debug