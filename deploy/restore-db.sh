#!/usr/bin/env bash
set -euo pipefail

# Run from the project root
cd "$(dirname "$0")/.."

BACKUP_FILE="db_backup/ai_data_agent.backup"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Database backup not found."
    exit 1
fi

echo "Checking PostgreSQL container..."

if ! sudo docker compose ps --status running --services | grep -qx postgres; then
    echo "ERROR: PostgreSQL container is not running."
    exit 1
fi

# Prevent accidental restoration over an existing database
TABLE_COUNT=$(sudo docker compose exec -T postgres \
    psql -U postgres -d postgres -t -A \
    -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")

if [ "$TABLE_COUNT" != "0" ]; then
    echo "ERROR: Database already contains tables. Restore cancelled."
    exit 1
fi

echo "Restoring database backup..."

# Stream the backup directly to pg_restore inside the container
sudo docker compose exec -T postgres \
    pg_restore \
    -U postgres \
    -d postgres \
    --no-owner \
    --no-acl \
    --clean \
    --if-exists \
    --exit-on-error \
    < "$BACKUP_FILE"

echo "Verifying restored tables..."

sudo docker compose exec -T postgres \
    psql -U postgres -d postgres -c "\dt"

echo "Database restoration completed."
