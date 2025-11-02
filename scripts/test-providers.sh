#!/bin/bash

# Test provider connectivity and API keys

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
else
    echo "ERROR: .env file not found"
    exit 1
fi

echo "================================================"
echo "Provider Connectivity Test"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test Google Places API
echo -e "${YELLOW}Testing Google Places API...${NC}"
if [ -z "$GOOGLE_PLACES_API_KEY" ]; then
    echo -e "${RED}✗ GOOGLE_PLACES_API_KEY not set${NC}"
else
    response=$(curl -s -X POST \
        "https://places.googleapis.com/v1/places:searchNearby" \
        -H "Content-Type: application/json" \
        -H "X-Goog-Api-Key: $GOOGLE_PLACES_API_KEY" \
        -H "X-Goog-FieldMask: places.id,places.displayName" \
        -d '{
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": 37.7749, "longitude": -122.4194},
                    "radius": 1000
                }
            },
            "maxResultCount": 1
        }' \
        2>&1)
    
    if echo "$response" | grep -q "error"; then
        echo -e "${RED}✗ Google Places API test failed${NC}"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
    else
        echo -e "${GREEN}✓ Google Places API working${NC}"
        echo "$response" | jq '.places[0].displayName // "No results"' 2>/dev/null
    fi
fi
echo ""

# Test Yelp Fusion API
echo -e "${YELLOW}Testing Yelp Fusion API...${NC}"
if [ -z "$YELP_API_KEY" ]; then
    echo -e "${RED}✗ YELP_API_KEY not set${NC}"
else
    response=$(curl -s -X GET \
        "https://api.yelp.com/v3/businesses/search?latitude=37.7749&longitude=-122.4194&limit=1" \
        -H "Authorization: Bearer $YELP_API_KEY" \
        2>&1)
    
    if echo "$response" | grep -q "error"; then
        echo -e "${RED}✗ Yelp Fusion API test failed${NC}"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
    else
        echo -e "${GREEN}✓ Yelp Fusion API working${NC}"
        echo "$response" | jq '.businesses[0].name // "No results"' 2>/dev/null
    fi
fi
echo ""

# Test OpenAI API
echo -e "${YELLOW}Testing OpenAI API...${NC}"
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}✗ OPENAI_API_KEY not set${NC}"
else
    response=$(curl -s -X POST \
        "https://api.openai.com/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $OPENAI_API_KEY" \
        -d '{
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "Say hi"}],
            "max_tokens": 5
        }' \
        2>&1)
    
    if echo "$response" | grep -q "error"; then
        echo -e "${RED}✗ OpenAI API test failed${NC}"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
    else
        echo -e "${GREEN}✓ OpenAI API working${NC}"
        echo "$response" | jq '.choices[0].message.content // "No response"' 2>/dev/null
    fi
fi
echo ""

echo "================================================"
echo "Test Complete"
echo "================================================"