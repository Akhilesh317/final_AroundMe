#!/bin/bash

# Around Me - Demo Script
# Demonstrates key features with sample queries

set -e

API_URL="${API_URL:-http://localhost:8000}"
DEMO_LAT="32.814"
DEMO_LNG="-96.948"

echo "================================================"
echo "Around Me - Feature Demonstration"
echo "================================================"
echo ""
echo "API URL: $API_URL"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to make API call and display results
demo_search() {
    local title="$1"
    local payload="$2"
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Demo: $title${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}Request:${NC}"
    echo "$payload" | jq '.'
    echo ""
    echo -e "${YELLOW}Response:${NC}"
    
    response=$(curl -s -X POST "$API_URL/api/search" \
        -H "Content-Type: application/json" \
        -d "$payload")
    
    echo "$response" | jq '{
        places_count: (.places | length),
        top_3_places: (.places[:3] | map({name, category, rating, score, distance_km})),
        debug: {
            cache_hit: .debug.cache_hit,
            agent_mode: .debug.agent_mode,
            ranking_preset: .debug.ranking_preset,
            total_time: .debug.timings.total
        }
    }'
    
    echo ""
    sleep 2
}

# Check if API is available
echo "Checking API health..."
if ! curl -s "$API_URL/api/health" > /dev/null; then
    echo "ERROR: API not available at $API_URL"
    echo "Please start the services first: docker compose -f deploy/compose.yml up"
    exit 1
fi
echo -e "${GREEN}✓ API is healthy${NC}"
echo ""
sleep 1

# Demo 1: Simple Query
demo_search "Simple Query - Coffee Shops" '{
  "query": "coffee",
  "lat": '$DEMO_LAT',
  "lng": '$DEMO_LNG',
  "radius_m": 3000,
  "top_k": 10
}'

# Demo 2: Query with Filters
demo_search "Query with Filters - Affordable Restaurants" '{
  "query": "restaurant",
  "lat": '$DEMO_LAT',
  "lng": '$DEMO_LNG',
  "radius_m": 5000,
  "filters": {
    "price": [1, 2],
    "open_now": false
  },
  "top_k": 10
}'

# Demo 3: Multi-Entity Query
demo_search "Multi-Entity Query - Restaurant near Park with Playground" '{
  "query": "family-friendly restaurant near park with playground",
  "lat": '$DEMO_LAT',
  "lng": '$DEMO_LNG',
  "radius_m": 3000,
  "multi_entity": {
    "entities": [
      {
        "kind": "restaurant",
        "must_haves": ["family_friendly"]
      },
      {
        "kind": "park",
        "must_haves": ["playground"]
      }
    ],
    "relations": [
      {
        "left": 0,
        "right": 1,
        "relation": "NEAR",
        "distance_m": 500
      }
    ],
    "radius_m": 3000,
    "top_k": 10
  }
}'

# Demo 4: Different Ranking Preset
demo_search "Nearby Ranking Preset - Prioritize Distance" '{
  "query": "cafe",
  "lat": '$DEMO_LAT',
  "lng": '$DEMO_LNG',
  "radius_m": 2000,
  "context": {
    "ranking_preset": "nearby"
  },
  "top_k": 10
}'

# Demo 5: Deterministic Mode (Faster)
demo_search "Deterministic Mode - No LLM" '{
  "query": "pizza",
  "lat": '$DEMO_LAT',
  "lng": '$DEMO_LNG',
  "radius_m": 3000,
  "context": {
    "agent_mode": "deterministic"
  },
  "top_k": 10
}'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Demo Complete!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Next steps:"
echo "  • Visit the Web UI: http://localhost:3000"
echo "  • View API docs: http://localhost:8000/docs"
echo "  • Check admin dashboard: http://localhost:3000/admin"
echo ""