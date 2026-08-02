# Backend image. ML extra is omitted by default (the hashing fallback keeps the
# image small); add `pip install -e ".[ml]"` for the real embedding model.
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY scripts ./scripts

RUN pip install --no-cache-dir -e .

EXPOSE 8000
# Seed the demo DB on first boot, then serve.
CMD ["sh", "-c", "python -m scripts.seed_demo && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
