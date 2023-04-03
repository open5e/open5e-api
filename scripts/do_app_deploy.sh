#!/bin/bash

set -euo pipefail

echo "Triggering deployment..."

curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" \
  -d '{"force_build": true}' \
  -o ./deploy.json \
  "https://api.digitalocean.com/v2/apps/$DIGITALOCEAN_APP_ID/deployments"

DEPLOYMENT_ID=$(jq -r '.deployment.id' ./deploy.json)
PHASE=$(jq -r '.deployment.phase' ./deploy.json)

COMPLETE_STATUSES="ACTIVE SUPERSEDED ERROR CANCELED"

# While the deployment is not complete, wait 10 seconds and check again.
while ! echo "$COMPLETE_STATUSES" | grep -q "$PHASE"; do
  echo "Deployment phase: $PHASE"
  sleep 10
  curl -s \
    -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" \
    -o ./deploy.json \
    "https://api.digitalocean.com/v2/apps/$DIGITALOCEAN_APP_ID/deployments/$DEPLOYMENT_ID"

  PHASE=$(jq -r '.deployment.phase' ./deploy.json)
done

if [ "$PHASE" = "ACTIVE" ]; then
  curl -s \
    -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" \
    -o ./app.json \
    "https://api.digitalocean.com/v2/apps/$DIGITALOCEAN_APP_ID"

  APP_URL=$(jq -r '.app.live_url' ./app.json)

  echo "Deployment complete. Your app is live at $APP_URL"

  exit 0
fi

echo "Deployment failed. Phase: $PHASE"
echo "Deployment logs: https://cloud.digitalocean.com/apps/$DIGITALOCEAN_APP_ID/deployments/$DEPLOYMENT_ID"

exit 1
