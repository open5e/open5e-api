FROM python:3.11-slim AS builder

WORKDIR /build

COPY --from=ghcr.io/astral-sh/uv:0.10 /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv run python manage.py quicksetup

FROM python:3.11-slim

WORKDIR /opt/services/open5e-api

COPY --from=builder /build/.venv ./.venv
COPY --from=builder /build/server ./server
COPY --from=builder /build/api ./api
COPY --from=builder /build/api_v2 ./api_v2
COPY --from=builder /build/search ./search
COPY --from=builder /build/templates ./templates
COPY --from=builder /build/staticfiles ./staticfiles
COPY --from=builder /build/db.sqlite3 ./db.sqlite3
COPY --from=builder /build/manage.py ./manage.py
COPY --from=builder /build/newrelic.ini ./newrelic.ini

ENV PATH="/opt/services/open5e-api/.venv/bin:$PATH"

CMD ["gunicorn", "-b", ":8888", "server.wsgi:application"]
