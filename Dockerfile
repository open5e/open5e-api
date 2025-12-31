FROM python:3.11-slim

RUN mkdir -p /opt/services/open5e-api
WORKDIR /opt/services/open5e-api

# Install dependencies
RUN pip install pipenv gunicorn

# Copy project files
COPY . /opt/services/open5e-api

# Install all dependencies from Pipfile
RUN pipenv install -v

# Download spaCy model for semantic search
RUN pipenv run python -m spacy download en_core_web_md

# Remove .env file (set your env vars via docker-compose.yml or your hosting provider)
RUN rm -f .env

# Run setup
RUN pipenv run python manage.py quicksetup

# Run gunicorn
CMD ["pipenv", "run", "gunicorn", "-b", ":8080", "--workers", "2", "--timeout", "120", "server.wsgi:application"]
