FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Generate entrypoint script directly in the image to avoid Windows CRLF issues
RUN printf '#!/bin/sh\nset -e\n\necho "Starting application..."\nexec uvicorn app.main:app --host 0.0.0.0 --port 8000\n' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
