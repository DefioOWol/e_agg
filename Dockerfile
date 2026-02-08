# Builder stage
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --exclude=./aggregator_app/tests/ ./aggregator_app /app

RUN pip install --no-cache-dir --upgrade uv && uv sync --frozen --no-dev


# Runner stage
FROM builder AS runner

COPY ./entrypoint.sh /app

RUN chmod +x /app/entrypoint.sh

CMD ["./entrypoint.sh"]


# Test stage
FROM builder AS test

RUN uv sync --frozen --dev

COPY ./aggregator_app/tests/ /app/tests/

CMD ["uv", "run", "pytest", "-v"]
