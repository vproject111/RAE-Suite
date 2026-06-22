#!/bin/bash
set -e
cd "$(dirname "$0")"

# Parse arguments for Development mode
DEV_MODE=false
for arg in "$@"; do
    if [ "$arg" == "--dev" ] || [ "$arg" == "-d" ]; then
        DEV_MODE=true
    fi
done

# Check if RAE_DATA_DIR is configured
if [ ! -f .env ] || ! grep -q "RAE_DATA_DIR" .env; then
    echo "⚠️  RAE-Suite is not configured! Starting interactive setup..."
    ./setup.sh
fi

# Load variables
source .env

# Ensure external networks are created (needed for included dev profiles)
docker network create rae-am-internal 2>/dev/null || true

if [ "$DEV_MODE" = true ]; then
    echo "🚀 Starting RAE Suite v3 Ultra in DEVELOPMENT mode (Hot-Reload)..."
    docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
else
    echo "🚀 Starting RAE Suite v3 Ultra in PRODUCTION mode..."
    docker compose up -d --build
fi

echo "⏳ Waiting for RAE Memory API to be ready..."
until curl -s http://localhost:8000/health > /dev/null; do
    sleep 2
    echo -n "."
done

echo -e "\n✅ RAE Memory API is ONLINE."
echo "🔄 Running Database Migrations..."
docker exec rae-memory alembic upgrade head

echo "✨ RAE Suite v3 Ultra is fully operational!"
docker ps

