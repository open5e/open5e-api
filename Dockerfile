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

# The release reported by /health. CI passes `git describe`; .git isn't in the build context.
ARG OPEN5E_RELEASE_ID=development
RUN uv run python manage.py build_info --release-id "$OPEN5E_RELEASE_ID"
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
COPY --from=builder /opt/services/open5e-api/pyproject.toml ./pyproject.toml
COPY --from=builder /opt/services/open5e-api/newrelic.ini ./newrelic.ini

ENV PATH="/opt/services/open5e-api/.venv/bin:$PATH" \
    WEB_CONCURRENCY=3 \
    GUNICORN_TIMEOUT=120

RUN python -m gunicorn --version

# /health returns 503 when the instance can't serve requests, which urlopen raises on.
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8888/health', timeout=4)"]

CMD ["sh", "-c", "python -m gunicorn -b :8888 -w ${WEB_CONCURRENCY} --timeout ${GUNICORN_TIMEOUT} server.wsgi:application"]
