FROM python:3.11-slim AS builder

WORKDIR /opt/services/open5e-api

COPY --from=ghcr.io/astral-sh/uv:0.10 /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv run python manage.py quicksetup

FROM python:3.11-slim

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

ENV PATH="/opt/services/open5e-api/.venv/bin:$PATH"

CMD ["gunicorn", "-b", ":8888", "server.wsgi:application"]
