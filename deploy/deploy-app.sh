#!/usr/bin/env bash
set -euo pipefail

# Go to project root
cd "$(dirname "$0")/.."

echo "Checking deployment files..."

if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found."
    exit 1
fi

if [ ! -f "docker-compose.yml" ]; then
    echo "ERROR: docker-compose.yml not found."
    exit 1
fi

# Restrict access to secrets
chmod 600 .env

echo "Pulling AI Data Agent Docker image..."
sudo docker compose pull ai-data-agent

echo "Starting containers..."
sudo docker compose up -d

echo "Checking container status..."
sudo docker compose ps

echo "Deployment commands completed."
