
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY docker/requirements-api.txt /tmp/requirements-api.txt

RUN pip install --no-cache-dir \
    -r /tmp/requirements-api.txt

RUN useradd --create-home --uid 10001 appuser

COPY src/media_platform/__init__.py \
     src/media_platform/api.py \
     src/media_platform/events.py \
     /app/src/media_platform/

USER appuser

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "media_platform.api:app", "--host", "0.0.0.0", "--port", "8080"]
