# WhatsApp webhook + jeans recommender for Google Cloud Run
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

COPY requirements-webhook.txt .
RUN pip install --no-cache-dir -r requirements-webhook.txt

COPY server.py .
COPY src/ ./src/
COPY data/processed/ ./data/processed/

# Single worker: conversation state is in-memory (StateManager).
CMD exec gunicorn \
    --bind 0.0.0.0:${PORT} \
    --workers 1 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    server:app
