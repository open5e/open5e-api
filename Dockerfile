FROM python:3.11-slim

# Install system dependencies including those needed for Elasticsearch
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Elasticsearch
RUN wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor -o /usr/share/keyrings/elasticsearch.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/elasticsearch.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | tee -a /etc/apt/sources.list.d/elastic-8.x.list && \
    apt-get update && \
    apt-get install -y elasticsearch && \
    rm -rf /var/lib/apt/lists/*

# Configure Elasticsearch for single-node setup
# Use sed to update existing settings or append if they don't exist
RUN sed -i '/^discovery.type:/d' /etc/elasticsearch/elasticsearch.yml && \
    sed -i '/^xpack.security.enabled:/d' /etc/elasticsearch/elasticsearch.yml && \
    sed -i '/^network.host:/d' /etc/elasticsearch/elasticsearch.yml && \
    sed -i '/^xpack.entitlement.enabled:/d' /etc/elasticsearch/elasticsearch.yml && \
    echo "discovery.type: single-node" >> /etc/elasticsearch/elasticsearch.yml && \
    echo "xpack.security.enabled: false" >> /etc/elasticsearch/elasticsearch.yml && \
    echo "network.host: 0.0.0.0" >> /etc/elasticsearch/elasticsearch.yml && \
    echo "xpack.entitlement.enabled: false" >> /etc/elasticsearch/elasticsearch.yml

# Ensure Elasticsearch directories exist and have correct permissions
# Note: The elasticsearch package already creates the elasticsearch user
RUN mkdir -p /var/lib/elasticsearch /var/log/elasticsearch && \
    chown -R elasticsearch:elasticsearch /etc/elasticsearch /var/lib/elasticsearch /var/log/elasticsearch

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

# Expose ports
EXPOSE 8080 9200

# Run startup script
CMD ["/start.sh"]