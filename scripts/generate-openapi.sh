#!/bin/bash

# Generate OpenAPI specification from FastAPI app

set -e

echo "Generating OpenAPI specification..."

# Start API temporarily if not running
API_URL="${API_URL:-http://localhost:8000}"

# Check if API is running
if ! curl -s "$API_URL/api/health" > /dev/null 2>&1; then
    echo "API not running. Please start it first:"
    echo "  docker compose -f deploy/compose.yml up api"
    exit 1
fi

# Fetch OpenAPI spec
curl -s "$API_URL/openapi.json" | jq '.' > packages/shared/openapi.json

if [ $? -eq 0 ]; then
    echo "✓ OpenAPI spec generated: packages/shared/openapi.json"
    
    # Generate TypeScript types if openapi-typescript is installed
    if command -v openapi-typescript &> /dev/null; then
        echo "Generating TypeScript types..."
        cd packages/shared
        npx openapi-typescript openapi.json -o openapi.ts
        echo "✓ TypeScript types generated: packages/shared/openapi.ts"
    else
        echo "Note: Install openapi-typescript to generate TypeScript types"
        echo "  npm install -g openapi-typescript"
    fi
else
    echo "✗ Failed to generate OpenAPI spec"
    exit 1
fi