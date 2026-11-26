#!/usr/bin/env bash

set -Eeuo pipefail

cd /opt/ai-data-agent

IMAGE="ghcr.io/rhishikesh-04/ai-powered-data-agent:latest"
SERVICE="ai-data-agent"
HEALTH_URL="http://127.0.0.1:8002/health"
ROLLBACK_IMAGE="ai-data-agent:rollback"

STATE_DIR="/var/lib/ai-data-agent"
FAILED_FILE="$STATE_DIR/failed-image"

mkdir -p "$STATE_DIR"

echo "[$(date)] Checking for application updates..."

CONTAINER_ID=$(docker compose ps -q "$SERVICE")

if [ -z "$CONTAINER_ID" ]; then
    echo "Application container not found."
    exit 1
fi

OLD_IMAGE=$(docker inspect --format '{{.Image}}' "$CONTAINER_ID")

docker compose pull "$SERVICE"

NEW_IMAGE=$(docker image inspect --format '{{.Id}}' "$IMAGE")

if [ "$OLD_IMAGE" = "$NEW_IMAGE" ]; then
    echo "No new image available."
    exit 0
fi

if [ -f "$FAILED_FILE" ]; then
    FAILED_IMAGE=$(cat "$FAILED_FILE")

    if [ "$NEW_IMAGE" = "$FAILED_IMAGE" ]; then
        echo "Skipping previously failed image."
        docker tag "$OLD_IMAGE" "$IMAGE"
        exit 0
    fi
fi

echo "New image detected."

docker tag "$OLD_IMAGE" "$ROLLBACK_IMAGE"

check_health() {
    for attempt in $(seq 1 12); do
        if curl -fsS --max-time 5 "$HEALTH_URL" > /dev/null; then
            return 0
        fi

        sleep 5
    done

    return 1
}

echo "Deploying updated application..."

if docker compose up -d --no-deps --force-recreate --pull never "$SERVICE" && check_health; then
    rm -f "$FAILED_FILE"
    echo "Deployment successful."
    exit 0
fi

echo "$NEW_IMAGE" > "$FAILED_FILE"

echo "Deployment failed. Starting rollback..."

docker tag "$ROLLBACK_IMAGE" "$IMAGE"

docker compose up -d --no-deps --force-recreate --pull never "$SERVICE"

if check_health; then
    echo "Rollback successful."
else
    echo "CRITICAL: Rollback health check failed."
fi

exit 1
