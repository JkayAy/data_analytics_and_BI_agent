FROM python:3.11-slim

WORKDIR /app

COPY apps/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/api/insightbridge ./insightbridge
COPY packages/semantic-layer /packages/semantic-layer

ENV SEMANTIC_LAYER_PATH=/packages/semantic-layer/metrics.yaml

EXPOSE 8000
CMD ["sh", "-c", "uvicorn insightbridge.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
