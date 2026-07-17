#!/bin/bash
# scripts/run_owasp_zap.sh
# Runs OWASP ZAP baseline API scan

API_URL=${RAE_API_URL:-"http://localhost:8000"}

if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker not found. Skipping OWASP ZAP DAST scan."
    exit 0
fi

echo "🛡️  Running OWASP ZAP baseline scan against $API_URL..."
# Run ZAP container targeting the API
docker run --network host -t ghcr.io/zaproxy/zaproxy:stable zap-api-scan.py \
    -t "$API_URL/openapi.json" -f openapi -r zap_report.html
