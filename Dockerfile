FROM python:3.11-slim

RUN mkdir -p /opt/services/open5e-api
WORKDIR /opt/services/open5e-api

# Install dependencies
RUN pip install pipenv gunicorn

# Copy project files
COPY . /opt/services/open5e-api

# Install all dependencies from Pipfile
RUN pipenv install -v

# Remove .env file (set your env vars via docker-compose.yml or your hosting provider)
RUN rm -f .env

# Copy startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Run startup script (handles migrations, quicksetup, and gunicorn)
CMD ["/start.sh"]
