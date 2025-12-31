#!/bin/bash
set -e

echo "Starting Open5e API..."

# Function to wait for Elasticsearch
wait_for_elasticsearch() {
    echo "Waiting for Elasticsearch to be ready..."
    
    # Default to elasticsearch service if ELASTICSEARCH_URL is not set
    ES_HOST="${ELASTICSEARCH_URL:-http://elasticsearch:9200}"
    
    # Remove trailing slash if present
    ES_HOST="${ES_HOST%/}"
    
    # Wait up to 120 seconds for Elasticsearch
    for i in {1..120}; do
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
    
    echo "❌ Elasticsearch failed to start within 240 seconds"
    exit 1
}

# Wait for Elasticsearch to be ready
wait_for_elasticsearch

# Navigate to the Django app directory
cd /opt/services/open5e-api

# Run Django setup (migrations, data loading, search indexing)
echo "🔄 Running Django quicksetup..."
echo "📋 Checking settings before quicksetup..."
pipenv run python -c "from server import settings; print(f'INCLUDE_V1_DATA: {settings.INCLUDE_V1_DATA}'); print(f'INCLUDE_V2_DATA: {settings.INCLUDE_V2_DATA}'); print(f'BUILD_V1_INDEX: {settings.BUILD_V1_INDEX}'); print(f'BUILD_V2_INDEX: {settings.BUILD_V2_INDEX}')"
echo "🚀 Starting quicksetup command..."
pipenv run python manage.py quicksetup --clean

# Start Gunicorn
echo "🚀 Starting Gunicorn server on port 8080..."
exec pipenv run gunicorn -b ":8080" --workers 2 --timeout 120 server.wsgi:application 