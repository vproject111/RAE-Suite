#!/bin/bash
# scripts/build_sbom_and_sign.sh
# Generates SBOM (CycloneDX) and signs the release binary/container with Cosign

if ! command -v cyclonedx-py &>/dev/null; then
    echo "⚠️  cyclonedx-py is not installed. Skipping SBOM generation."
    exit 0
fi

echo "📦 Generating CycloneDX SBOM..."
cyclonedx-py poetry -o sbom.json

if ! command -v cosign &>/dev/null; then
    echo "⚠️  cosign is not installed. Skipping artifact signing."
    exit 0
fi

if [ -f "cosign.key" ]; then
    echo "🖋️  Signing SBOM with Cosign..."
    cosign sign-blob --key cosign.key --tlog-upload=false sbom.json
fi
