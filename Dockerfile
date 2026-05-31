FROM python:3.11-slim AS builder

WORKDIR /build

COPY --from=ghcr.io/astral-sh/uv:0.10 /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv run python manage.py quicksetup

FROM python:3.11-slim

WORKDIR /opt/services/open5e-api

COPY --from=builder /build/.venv /opt/services/open5e-api/.venv
COPY --from=builder /build /opt/services/open5e-api

ENV PATH="/opt/services/open5e-api/.venv/bin:$PATH"

CMD ["gunicorn", "-b", ":8888", "server.wsgi:application"]
