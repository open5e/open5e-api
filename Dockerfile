FROM python:3.11-slim

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/services/open5e-api
WORKDIR /opt/services/open5e-api
# copy our project code

# install our dependencies
RUN pip install pipenv gunicorn
COPY . /opt/services/open5e-api

# Install only basic dependencies first (excluding heavy ML packages)
RUN pipenv install --skip-lock django djangorestframework django-filter django-cors-headers newrelic requests whitenoise gunicorn drf-spectacular elasticsearch django-haystack

# migrate the db, load basic content (without ML search indexing initially)
RUN pipenv run python manage.py quicksetup --noindex

# remove .env file (set your env vars via docker-compose.yml or your hosting provider)
RUN rm .env

# Create startup script that installs ML packages and builds search index at runtime
RUN echo '#!/bin/bash\n\
set -e\n\
echo "=== Starting Open5e API ==="\n\
echo "Installing ML dependencies in background..."\n\
(\n\
  echo "Installing sentence-transformers, torch, scikit-learn, numpy..."\n\
  pipenv install sentence-transformers torch scikit-learn numpy\n\
  echo "ML dependencies installed, building search index..."\n\
  pipenv run python manage.py quicksetup\n\
  echo "=== ML search features now available ==="\n\
) &\n\
echo "Starting server with basic search functionality..."\n\
exec pipenv run gunicorn -b :8888 server.wsgi:application' > /opt/services/open5e-api/start.sh

RUN chmod +x /opt/services/open5e-api/start.sh

# Run the startup script
CMD ["/opt/services/open5e-api/start.sh"]