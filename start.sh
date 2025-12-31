#!/bin/bash
set -e

echo "Starting Open5e API..."

# Check if Elasticsearch is installed in this container (from Dockerfile.with-elasticsearch)
if [ -f /usr/share/elasticsearch/bin/elasticsearch ]; then
    echo "🔍 Elasticsearch detected in container, starting it..."
    
    # Ensure directories exist and have correct permissions
    mkdir -p /var/lib/elasticsearch /var/log/elasticsearch /var/run/elasticsearch
    chown -R elasticsearch:elasticsearch /var/lib/elasticsearch /var/log/elasticsearch /var/run/elasticsearch
    
    # Start Elasticsearch in the background as elasticsearch user
    # Elasticsearch refuses to run as root, so we must run as elasticsearch user
    # Disable set -e temporarily to handle command failures gracefully
    set +e
    if command -v runuser >/dev/null 2>&1; then
        runuser -u elasticsearch -- /usr/share/elasticsearch/bin/elasticsearch -d -p /var/run/elasticsearch/elasticsearch.pid
        ES_STARTED=$?
    elif command -v su >/dev/null 2>&1; then
        su -s /bin/bash elasticsearch -c "/usr/share/elasticsearch/bin/elasticsearch -d -p /var/run/elasticsearch/elasticsearch.pid"
        ES_STARTED=$?
    elif command -v sudo >/dev/null 2>&1; then
        sudo -u elasticsearch /usr/share/elasticsearch/bin/elasticsearch -d -p /var/run/elasticsearch/elasticsearch.pid
        ES_STARTED=$?
    else
        echo "⚠️  No suitable command found to run as elasticsearch user (tried runuser, su, sudo)"
        echo "⚠️  Attempting to start as current user (may fail if running as root)..."
        /usr/share/elasticsearch/bin/elasticsearch -d -p /var/run/elasticsearch/elasticsearch.pid
        ES_STARTED=$?
    fi
    set -e
    
    if [ $ES_STARTED -ne 0 ]; then
        echo "❌ Failed to start Elasticsearch, will proceed without it"
    else
        echo "✅ Elasticsearch started successfully"
    fi
    
    # Set ELASTICSEARCH_URL to localhost if not already set
    export ELASTICSEARCH_URL="${ELASTICSEARCH_URL:-http://127.0.0.1:9200/}"
    echo "📍 Using Elasticsearch at $ELASTICSEARCH_URL"
else
    echo "ℹ️  Elasticsearch not found in container, expecting external service"
fi

# Function to wait for Elasticsearch
wait_for_elasticsearch() {
    echo "Waiting for Elasticsearch to be ready..."
    
    # Default to localhost if ES is in container, otherwise use elasticsearch service name
    ES_HOST="${ELASTICSEARCH_URL:-http://127.0.0.1:9200}"
    
    # If ELASTICSEARCH_URL is not set and ES is not in container, try docker-compose service name
    if [ -z "${ELASTICSEARCH_URL:-}" ] && [ ! -f /usr/share/elasticsearch/bin/elasticsearch ]; then
        ES_HOST="http://elasticsearch:9200"
    fi
    
    # Remove trailing slash if present
    ES_HOST="${ES_HOST%/}"
    
    # Wait up to 120 seconds for Elasticsearch (needs more time when starting in container)
    for i in {1..60}; do
        echo "Attempt $i: Checking Elasticsearch at $ES_HOST"
        
        # Check cluster health and that it can accept index operations
        if curl -f -s "$ES_HOST/_cluster/health?wait_for_status=yellow&timeout=5s" > /dev/null 2>&1; then
            echo "✅ Elasticsearch cluster is healthy!"
            
            # Test that we can create/query indices
            echo "🔍 Testing index operations..."
            if curl -f -s -X PUT "$ES_HOST/test-connection-index" > /dev/null 2>&1 && \
               curl -f -s -X DELETE "$ES_HOST/test-connection-index" > /dev/null 2>&1; then
                echo "✅ Elasticsearch is fully ready for indexing!"
                return 0
            else
                echo "⏳ Elasticsearch responding but not ready for indexing yet..."
            fi
        else
            echo "⏳ Elasticsearch not ready yet, waiting 2 seconds..."
        fi
        
        sleep 2
    done
    
    echo "❌ Elasticsearch failed to start within 120 seconds"
    echo "🔄 Falling back to SQLite FTS mode for deployment"
    echo "⚠️  Note: Vector search will be disabled, but text and fuzzy search will work"
    # Continue with SQLite-only mode instead of failing
    export ELASTICSEARCH_AVAILABLE=false
    return 0
}

# Wait for Elasticsearch to be ready (or fall back to SQLite)
wait_for_elasticsearch

# Navigate to the Django app directory
cd /opt/services/open5e-api

# Run Django setup (migrations, data loading, search indexing)
echo "🔄 Running Django quicksetup..."
echo "📋 Checking settings before quicksetup..."
pipenv run python -c "from server import settings; print(f'INCLUDE_V1_DATA: {settings.INCLUDE_V1_DATA}'); print(f'INCLUDE_V2_DATA: {settings.INCLUDE_V2_DATA}'); print(f'BUILD_V1_INDEX: {settings.BUILD_V1_INDEX}'); print(f'BUILD_V2_INDEX: {settings.BUILD_V2_INDEX}')"

if [ "${ELASTICSEARCH_AVAILABLE:-true}" = "false" ]; then
    echo "🗄️  Running quicksetup in SQLite FTS mode (Elasticsearch not available)..."
    pipenv run python manage.py quicksetup --clean || {
        echo "⚠️  Quicksetup had issues, but continuing with basic setup..."
        pipenv run python manage.py migrate
        pipenv run python manage.py collectstatic --noinput
    }
else
    echo "🔍 Running quicksetup with full Elasticsearch support..."
    pipenv run python manage.py quicksetup --clean
fi

# Start Gunicorn
echo "🚀 Starting Gunicorn server on port 8080..."
exec pipenv run gunicorn -b ":8080" --workers 2 --timeout 120 server.wsgi:application 