FROM python:3.11-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.10.7 /uv /uvx /usr/local/bin/

WORKDIR /opt/services/open5e-api

ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv run python manage.py quicksetup
RUN uv run python -m gunicorn --version

FROM python:3.11-slim-bookworm

WORKDIR /opt/services/open5e-api

COPY --from=builder /opt/services/open5e-api/.venv ./.venv
COPY --from=builder /opt/services/open5e-api/server ./server
COPY --from=builder /opt/services/open5e-api/api ./api
COPY --from=builder /opt/services/open5e-api/api_v2 ./api_v2
COPY --from=builder /opt/services/open5e-api/search ./search
COPY --from=builder /opt/services/open5e-api/templates ./templates
COPY --from=builder /opt/services/open5e-api/staticfiles ./staticfiles
COPY --from=builder /opt/services/open5e-api/db.sqlite3 ./db.sqlite3
COPY --from=builder /opt/services/open5e-api/manage.py ./manage.py
COPY --from=builder /opt/services/open5e-api/newrelic.ini ./newrelic.ini

ENV PATH="/opt/services/open5e-api/.venv/bin:$PATH" \
    WEB_CONCURRENCY=3 \
    GUNICORN_TIMEOUT=120

RUN python -m gunicorn --version

CMD ["sh", "-c", "python -m gunicorn -b :8888 -w ${WEB_CONCURRENCY} --timeout ${GUNICORN_TIMEOUT} server.wsgi:application"]
