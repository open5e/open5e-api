FROM python:3.11-slim

# Add system dependencies for building packages
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/services/open5e-api
WORKDIR /opt/services/open5e-api
# copy our project code

# install our dependencies
RUN pip install pipenv gunicorn

# Copy project files
COPY . /opt/services/open5e-api

# Install all dependencies from Pipfile
RUN pipenv install -v

# remove .env file (set your env vars via docker-compose.yml or your hosting provider)
RUN rm -f .env

# Create startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Run startup script
CMD ["/start.sh"]