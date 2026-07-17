#!/bin/bash
# scripts/run_schemathesis.sh
# Runs contract fuzzing using schemathesis against the OpenAPI schema

if ! command -v schemathesis &> /dev/null; then
    echo "⚠️  schemathesis is not installed. Skipping API contract fuzzing."
    exit 0
fi

API_URL=${RAE_API_URL:-"http://localhost:8000"}
echo "🔥 Running Schemathesis API fuzzing against $API_URL/openapi.json..."
schemathesis run "$API_URL/openapi.json" --checks all --workers 4
