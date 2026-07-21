FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN pip install --no-cache-dir poetry==1.8.3

COPY pyproject.toml ./
RUN poetry install --no-root --no-interaction --with dev

COPY . .
RUN poetry install --no-interaction --with dev

FROM base AS dev
EXPOSE 8000
CMD ["uvicorn", "afridock_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS production
ENV POETRY_VIRTUALENVS_CREATE=false
RUN poetry install --no-interaction --only main
EXPOSE 8000
CMD ["gunicorn", "afridock_api.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "2"]
