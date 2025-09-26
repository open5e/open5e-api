#!/bin/bash

# Script to poll deployments and clear Cloudflare cache
# Required environment variables:
# - DIGITALOCEAN_TOKEN: Your DigitalOcean API token
# - CLOUDFLARE_TOKEN: Your Cloudflare API token
# Usage: ./clear_cloudflare_cache.sh [commit_hash]
#   If commit_hash is not provided, will use current commit

set -e

# Check for required environment variables
if [ -z "$DIGITALOCEAN_TOKEN" ] || [ -z "$CLOUDFLARE_TOKEN" ]; then
    echo "Error: Required environment variables are not set"
    echo "Please set the following environment variables:"
    echo "- DIGITALOCEAN_TOKEN: Your DigitalOcean API token"
    echo "- CLOUDFLARE_TOKEN: Your Cloudflare API token"
    exit 1
fi

# Use provided commit hash or fall back to current commit
CURRENT_COMMIT=${1:-$(git rev-parse HEAD)}

echo "Initial 30 second delay..."
sleep 30

APP_IDS="52a99a96-7e6a-4258-b523-23d615c05571,7917c4fa-2426-4f51-b8cd-15a680fcaf1f,7f68aa01-e022-4244-81a4-0e5a50893703,476726eb-3be5-4b53-abeb-fba6db77786e"
echo "Current commit: $CURRENT_COMMIT"

for attempt in {1..20}; do
    echo "Check attempt $attempt of 20..."
    
    for app_id in ${APP_IDS//,/ }; do
        echo "Checking app: $app_id"
        response=$(curl -s \
            -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" \
            -H "Content-Type: application/json" \
            "https://api.digitalocean.com/v2/apps/$app_id/deployments?page=1&per_page=1")
        
        created_at=$(echo $response | jq -r '.deployments[0].created_at')
        status=$(echo $response | jq -r '.deployments[0].phase')
        commit_hash=$(echo $response | jq -r '.deployments[0].services[0].source_commit_hash')
        
        echo "Latest deployment status: $status (created: $created_at, commit: $commit_hash)"
        
        # Check if deployment is from last 10 minutes, is active, and either matches our commit or is null (manual deployments)
        if [ "$status" = "ACTIVE" ] && \
           [ $(( $(date +%s) - $(date -d "$created_at" +%s) )) -lt 600 ] && \
           ( [ "$commit_hash" = "$CURRENT_COMMIT" ] || [ "$commit_hash" = "null" ] ); then
            echo "Found recent successful deployment matching our criteria"
            
            echo "Purging Cloudflare cache..."
            response=$(curl -s -X POST \
                "https://api.cloudflare.com/client/v4/zones/04102fd3a28043d9d40a2688282d688a/purge_cache" \
                -H "Authorization: Bearer $CLOUDFLARE_TOKEN" \
                -H "Content-Type: application/json" \
                --data '{"purge_everything":true}')
            
            if [ "$(echo $response | jq -r '.success')" = "true" ]; then
                echo "Successfully purged Cloudflare cache"
                exit 0
            else
                echo "Failed to purge cache:"
                echo $response
                exit 1
            fi
        fi
    done
    
    if [ $attempt -eq 20 ]; then
        echo "Timeout after 10 minutes - no matching successful deployments found"
        exit 1
    fi
    
    echo "No matching successful deployments yet, waiting 30 seconds..."
    sleep 30
done 