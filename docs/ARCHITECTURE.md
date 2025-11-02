# Around Me - Architecture Documentation

## Overview

Around Me is a full-stack local discovery platform that uses agentic AI to interpret natural language queries, fuse data from multiple providers, and deliver ranked, explainable results with support for complex multi-entity constraints and conversational refinement.

## System Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                        Next.js Web App                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Search  │  │ Results  │  │  Place   │  │ Profile  │   │
│  │   Page   │  │   Page   │  │ Details  │  │   Page   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/JSON
┌─────────────────────▼───────────────────────────────────────┐
│                     FastAPI Backend                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              LangGraph Agent Pipeline                │   │
│  │  ┌─────────┐  ┌────────┐  ┌─────────┐  ┌────────┐  │   │
│  │  │ Parse   │→ │  Plan  │→ │  Call   │→ │ Fuse & │  │   │
│  │  │ Intent  │  │        │  │Providers│  │ Dedupe │  │   │
│  │  └─────────┘  └────────┘  └─────────┘  └────────┘  │   │
│  │       │                         │                    │   │
│  │       ▼                         ▼                    │   │
│  │  ┌─────────┐  ┌────────┐  ┌─────────┐  ┌────────┐  │   │
│  │  │Constraint│→ │ Score  │→ │Validate │→ │ Format │  │   │
│  │  │  Join   │  │ & Rank │  │         │  │ Answer │  │   │
│  │  └─────────┘  └────────┘  └─────────┘  └────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Google    │  │     Yelp     │  │     LLM      │      │
│  │  Places v1  │  │    Fusion    │  │   Adapter    │      │
│  └─────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│              Data Layer                                       │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │  PostgreSQL  │         │    Redis     │                  │
│  │  - Profiles  │         │  - Cache     │                  │
│  │  - Prefs     │         │  - Sessions  │                  │
│  │  - Logs      │         │  - Results   │                  │
│  └──────────────┘         └──────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## Agent Graph (LangGraph)

### Node Flow
```
ParseIntent → Plan → CallProviders → FuseDedupe → ConstraintJoin 
    → ScoreRank → Validate → FormatAnswer
```

### Node Descriptions

#### 1. ParseIntent
**Purpose**: Parse natural language query into structured intent

**Modes**:
- **Full**: Uses LLM to parse complex queries
- **Deterministic**: Simple rule-based parsing

**Output**:
```json
{
  "type": "simple" | "multi_entity",
  "query": "coffee",
  "category": "cafe",
  "filters": { "price": [1, 3], "open_now": true }
}
```

**Multi-Entity Output**:
```json
{
  "type": "multi_entity",
  "entities": [
    { "kind": "restaurant", "must_haves": ["changing_station"] },
    { "kind": "park", "must_haves": ["playground"] }
  ],
  "relations": [
    { "left": 0, "right": 1, "relation": "NEAR", "distance_m": 500 }
  ]
}
```

#### 2. Plan
**Purpose**: Decide which providers and endpoints to call

**Logic**:
- Use text search for specific queries (brands, cuisines)
- Use nearby search for generic queries
- Always call both providers for coverage

#### 3. CallProviders
**Purpose**: Execute parallel provider calls

**Features**:
- Async HTTP with retries and exponential backoff
- Pagination handling
- Rate limit respect
- Normalization to `ProviderPlace` schema

#### 4. FuseDedupe
**Purpose**: Merge and deduplicate results across providers

**Algorithm**:
1. Normalize names (lowercase, strip suffixes)
2. Calculate similarity: RapidFuzz partial_ratio ≥ 82%
3. Check distance: Haversine ≤ 120m
4. Cluster using union-find
5. Select representative (highest review count → rating → Google preference)

**Output**: List of deduplicated `ProviderPlace` objects with full provenance

#### 5. ConstraintJoin
**Purpose**: Apply multi-entity spatial constraints

**Logic**:
- For single-entity: pass through
- For multi-entity:
  1. Filter each entity by must_haves
  2. Find nearest neighbors satisfying relations
  3. Keep only anchors with all required partners
  4. Attach `matchedPartners[]` to results

**Complexity**: O(n*m) where n=anchors, m=partners per relation

#### 6. ScoreRank
**Purpose**: Score and rank places with explainability

**Formula**:
```
base_score = 0.55*(rating/5) + 0.30*min(1, log1p(reviews)/8) + 0.15*(1 - min(dist,10)/10)

bonuses:
- open_now: +0.06 if matches filter
- price_fit: +0.05 if in range, -0.03 if far
- preferences: +0.0 to +0.15 (bounded)

final_score = base_score + bonuses
```

**Presets**:
| Preset | Rating | Reviews | Distance |
|--------|--------|---------|----------|
| balanced | 0.55 | 0.30 | 0.15 |
| nearby | 0.35 | 0.20 | 0.45 |
| review-heavy | 0.45 | 0.50 | 0.05 |

**Evidence**: Each score component tracked in `evidence` dict

#### 7. Validate
**Purpose**: Check result quality and suggest fallbacks

**Checks**:
- Result count > 0
- Result count sufficient (≥5 preferred)
- Geographic coverage

**Actions**:
- Suggest radius expansion if needed
- Log issues for debugging

#### 8. FormatAnswer
**Purpose**: Build final `SearchResponse`

**Output**:
```json
{
  "places": [...],
  "debug": {
    "timings": { "total": 1.234, "google": 0.567, ... },
    "cache_hit": false,
    "agent_trace_id": "trace-abc123",
    "counts_before_after": { "google": 20, "yelp": 15, "fused": 30 },
    "ranking_preset": "balanced",
    "constraints_satisfied": { "kept": 10, "dropped": 5 }
  },
  "result_set_id": "result-xyz"
}
```

## Provider Integration

### Google Places API v1

**Endpoints**:
- `/places:searchNearby` - Radius search
- `/places:searchText` - Text search with location bias

**Headers**:
```
X-Goog-Api-Key: <key>
X-Goog-FieldMask: places.id,places.displayName,places.location,...
```

**Field Mask Strategy**:
- Request only needed fields to minimize costs
- Include: id, name, location, rating, reviews, price, phone, website, maps_url, address, hours, types

**Pagination**:
- Max 20 results per request
- Use `nextPageToken` with 2-second delays
- Stop at `max_results` or no more pages

**Normalization**:
```python
{
  "displayName": {"text": "Blue Bottle"} → name: "Blue Bottle"
  "location": {"latitude": 37.77, "longitude": -122.41} → lat/lng
  "priceLevel": "PRICE_LEVEL_MODERATE" → price_level: 2
  "rating": 4.5 → rating: 4.5
  "userRatingCount": 1250 → user_rating_count: 1250
}
```

### Yelp Fusion API

**Endpoint**:
- `/v3/businesses/search`

**Parameters**:
- `latitude`, `longitude`, `radius` (max 40km)
- `term` for query
- `categories` for filtering
- `limit` (max 50 per request)
- `offset` for pagination

**Price Mapping**:
```
"$" → 1, "$$" → 2, "$$$" → 3, "$$$$" → 4
```

**Normalization**:
```python
{
  "name": "Philz Coffee" → name
  "coordinates": {...} → lat/lng
  "rating": 4.5 → rating
  "review_count": 800 → user_rating_count
  "price": "$$" → price_level: 2
  "url": "..." → website & maps_url
}
```

### Error Handling

**Retry Strategy**:
- Max 3 retries
- Exponential backoff: 2^attempt seconds
- Retry on 5xx errors only
- Log all failures with trace ID

**Graceful Degradation**:
- If one provider fails, continue with other
- Return partial results with debug info
- Never fail entire search due to one provider

## Deduplication Algorithm

### Name Normalization
```python
def normalize_name(name: str) -> str:
    name = name.lower()
    # Remove suffixes
    for suffix in [", inc", ", llc", " inc.", ...]:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    # Remove punctuation
    name = re.sub(r'[.,!?;:"\']', '', name)
    # Normalize whitespace
    name = ' '.join(name.split())
    return name
```

### Similarity Check
```python
def are_duplicates(p1, p2) -> bool:
    name_sim = fuzz.partial_ratio(
        normalize_name(p1.name),
        normalize_name(p2.name)
    )
    geo_dist = haversine(
        (p1.lat, p1.lng),
        (p2.lat, p2.lng),
        unit=Unit.METERS
    )
    return name_sim >= 82 and geo_dist <= 120
```

### Union-Find Clustering
```python
def cluster_duplicates(places):
    parent = list(range(len(places)))
    
    def find(i):
        if parent[i] != i:
            parent[i] = find(parent[i])
        return parent[i]
    
    def union(i, j):
        root_i, root_j = find(i), find(j)
        if root_i != root_j:
            parent[root_j] = root_i
    
    # Find all duplicate pairs
    for i in range(len(places)):
        for j in range(i+1, len(places)):
            if are_duplicates(places[i], places[j]):
                union(i, j)
    
    # Group by cluster
    clusters = {}
    for i in range(len(places)):
        root = find(i)
        clusters.setdefault(root, []).append(places[i])
    
    return list(clusters.values())
```

### Representative Selection
```python
def select_representative(cluster):
    return max(cluster, key=lambda p: (
        p.user_rating_count or 0,
        p.rating or 0,
        0 if p.provider == 'google' else 1  # Prefer Google
    ))
```

## Multi-Entity Constraints

### Constraint Types

**NEAR**: Generic proximity (default 500m)
```json
{"left": 0, "right": 1, "relation": "NEAR"}
```

**WITHIN_DISTANCE**: Specific distance
```json
{"left": 0, "right": 1, "relation": "WITHIN_DISTANCE", "distance_m": 300}
```

### Resolution Algorithm
```python
async def resolve_constraints(entities, relations):
    # 1. Search each entity independently
    entity_results = {}
    for i, entity in enumerate(entities):
        results = await search_entity(entity)
        # Filter by must_haves
        filtered = [p for p in results if has_features(p, entity.must_haves)]
        entity_results[i] = filtered
    
    # 2. Apply spatial joins
    anchors = entity_results[0]
    final_results = []
    
    for anchor in anchors:
        matched_partners = []
        all_satisfied = True
        
        for relation in relations:
            if relation.left != 0:
                continue
            
            partners = entity_results[relation.right]
            max_dist = relation.distance_m or 500
            
            # Find nearest partner within max_dist
            nearest = find_nearest(anchor, partners, max_dist)
            
            if nearest:
                matched_partners.append(nearest)
            else:
                all_satisfied = False
                break
        
        if all_satisfied:
            anchor.matched_partners = matched_partners
            final_results.append(anchor)
    
    return final_results
```

### Performance Optimization

**Spatial Indexing** (future):
- R-tree or quad-tree for partner lookups
- Current: O(n*m) brute force acceptable for <1000 places

**Caching**:
- Cache entity results by kind + must_haves
- TTL: 10 minutes

## Conversational Follow-ups

### Session Management

**Storage**:
- Redis key: `result_set:{uuid}`
- TTL: 15 minutes
- Content: Serialized `Place[]`

**Context Linking**:
```json
{
  "conversation_id": "conv-123",
  "result_set_id": "result-456",
  "follow_up": true
}
```

### Refinement Logic
```python
async def handle_followup(request, previous_places):
    filtered = []
    
    for place in previous_places:
        # Apply new filters
        if request.filters.price:
            if not in_price_range(place, request.filters.price):
                continue
        
        # Check new must_haves from query
        must_haves = extract_must_haves(request.query)
        if must_haves:
            if not has_features(place, must_haves):
                continue
        
        filtered.append(place)
    
    # If empty and semantics allow, suggest broadening
    if not filtered and should_expand(request):
        return await expand_search(request)
    
    return filtered
```

### UI Flow

1. Initial search → Store result_set_id
2. User refines → Send with result_set_id + follow_up=true
3. Backend filters → Return subset
4. Display "Showing X of Y from previous results"

## Personalization

### Opt-In Flow

1. User sees prompt: "Save this as a preference?"
2. User opts in → Profile created
3. Preferences stored in DB
4. Applied to future searches

### Storage Schema
```sql
CREATE TABLE profiles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE profile_preferences (
    id SERIAL PRIMARY KEY,
    profile_id INT REFERENCES profiles(id) ON DELETE CASCADE,
    key VARCHAR(255) NOT NULL,
    value VARCHAR(255) NOT NULL,
    weight FLOAT DEFAULT 0.5,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Preference Application
```python
def apply_personalization(score, evidence, place, preferences):
    total_boost = 0.0
    
    for pref in preferences:
        if pref.key == 'category' and place.category == pref.value:
            total_boost += 0.05 * pref.weight
        elif pref.key == 'type' and pref.value in place.types:
            total_boost += 0.04 * pref.weight
        elif pref.key.startswith('feat_'):
            if place.features.get(pref.key, 0) > 0.5:
                total_boost += 0.03 * pref.weight
    
    # Cap at max_personalization_boost (0.15)
    total_boost = min(total_boost, 0.15)
    
    if total_boost > 0:
        evidence['preferences'] = total_boost
        score += total_boost
    
    return score, evidence
```

### Privacy & Control

- Default: OFF
- User must explicitly enable
- Full CRUD via API
- DELETE removes all preferences
- No cross-user data sharing

## Caching Strategy

### Cache Key Generation
```python
def generate_cache_key(query, lat, lng, radius, filters, ranking_preset, multi_entity):
    parts = [
        query or "",
        f"{lat:.6f}",
        f"{lng:.6f}",
        str(radius),
        ranking_preset,
        json.dumps(filters, sort_keys=True) if filters else "",
        json.dumps(multi_entity, sort_keys=True) if multi_entity else "",
    ]
    key_string = "|".join(parts)
    return f"search:{hashlib.sha256(key_string.encode()).hexdigest()[:16]}"
```

### TTL Strategy

| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| Search results | 20 min | Balance freshness & cost |
| Result sets | 15 min | Support follow-up window |
| Conversations | 15 min | Session-based context |
| Preferences | N/A | Postgres (durable) |

### Invalidation

**Automatic**:
- TTL expiration

**Manual** (future):
- On provider data updates
- On preference changes (partial)

## Database Schema
```sql
-- Search audit log
CREATE TABLE search_logs (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(255),
    request_json JSONB NOT NULL,
    response_meta JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_search_logs_conversation ON search_logs(conversation_id);

-- Saved searches
CREATE TABLE saved_searches (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    request_json JSONB NOT NULL,
    results_snapshot JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_saved_searches_user ON saved_searches(user_id);

-- User feedback
CREATE TABLE feedback (
    id SERIAL PRIMARY KEY,
    place_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    thumbs_up BOOLEAN NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_feedback_place ON feedback(place_id);

-- Profiles (personalization)
CREATE TABLE profiles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE profile_preferences (
    id SERIAL PRIMARY KEY,
    profile_id INT REFERENCES profiles(id) ON DELETE CASCADE,
    key VARCHAR(255) NOT NULL,
    value VARCHAR(255) NOT NULL,
    weight FLOAT DEFAULT 0.5 CHECK (weight >= 0 AND weight <= 1),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_prefs_profile ON profile_preferences(profile_id);
```

## API Contracts

### POST /api/search

**Request**:
```typescript
interface SearchRequest {
  query?: string
  lat: number  // -90 to 90
  lng: number  // -180 to 180
  radius_m: number  // 100 to 50000
  filters?: {
    price?: [number, number]  // 0-4
    open_now?: boolean
    category?: string | string[]
  }
  multi_entity?: MultiEntityIntent
  context?: {
    conversation_id?: string
    result_set_id?: string
    follow_up?: boolean
    agent_mode?: 'full' | 'deterministic'
    ranking_preset?: 'balanced' | 'nearby' | 'review-heavy'
  }
  top_k?: number  // 1 to 100
}
```

**Response**:
```typescript
interface SearchResponse {
  places: Place[]
  debug: {
    timings: Record<string, number>
    cache_hit: boolean
    agent_trace_id: string
    counts_before_after: Record<string, number>
    ranking_preset: string
    constraints_satisfied: Record<string, any>
    agent_mode: string
  }
  result_set_id: string
}
```

### GET /api/profile/preferences

**Query**: `user_id=string`

**Response**:
```typescript
interface PreferenceListResponse {
  preferences: Array<{
    id: number
    profile_id: number
    key: string
    value: string
    weight: number
    updated_at: string
  }>
}
```

## Performance Characteristics

### Latency Budget

| Component | Target | P99 |
|-----------|--------|-----|
| Parse Intent (LLM) | <200ms | 500ms |
| Provider Calls (parallel) | <800ms | 1500ms |
| Dedupe | <100ms | 200ms |
| Ranking | <50ms | 100ms |
| **Total** | <1.5s | 3s |

### Throughput

- **Rate Limit**: 60 req/min per IP (configurable)
- **Concurrency**: 20 concurrent provider connections
- **Cache Hit Rate**: Target 40% after warmup

### Scalability

**Current** (single instance):
- ~10-20 searches/second
- Limited by provider API quotas

**Future** (horizontal scaling):
- Load balancer → Multiple API instances
- Shared Redis cluster
- Postgres read replicas

## Error Handling

### Error Response Format (RFC 7807)
```json
{
  "type": "provider-error",
  "title": "ProviderError",
  "status": 502,
  "detail": "Google Places error: HTTP 429: Rate limit exceeded",
  "trace_id": "trace-abc123",
  "extensions": {
    "provider": "google"
  }
}
```

### Error Types

| Type | Status | Description |
|------|--------|-------------|
| validation-error | 422 | Invalid input |
| not-found | 404 | Resource not found |
| provider-error | 502 | External API failure |
| internal-error | 500 | Unexpected error |

### Retry Logic

**Transient Errors** (retry):
- Network timeouts
- 5xx from providers
- Rate limit (with backoff)

**Permanent Errors** (fail fast):
- 4xx client errors
- Invalid API keys
- Malformed responses

## Security

### API Key Management

- Environment variables only
- Never logged
- Rotate quarterly

### Rate Limiting

- slowapi middleware
- IP-based (production: user-based)
- 60 requests/minute default

### Input Validation

- Pydantic strict validation
- Coordinate bounds checked
- SQL injection: Use SQLAlchemy ORM
- XSS: React escapes by default

### CORS

- Whitelist: `localhost:3000` (dev), production domain
- Credentials: Allowed
- Methods: GET, POST, PUT, DELETE

## Monitoring & Observability

### Structured Logging

**Format**: JSON
**Fields**:
- `timestamp`: ISO 8601
- `level`: INFO, WARNING, ERROR
- `trace_id`: UUID per request
- `event`: Structured event name
- `context`: Event-specific data

**Example**:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "trace_id": "trace-abc123",
  "event": "search_complete",
  "places_count": 25,
  "duration_s": 1.234
}
```

### Metrics

**Counters**:
- `searches_total`
- `provider_calls_total{provider}`
- `cache_hits_total`
- `cache_misses_total`

**Histograms**:
- `search_duration_seconds`
- `provider_call_duration_seconds{provider}`
- `ranking_duration_seconds`

### Health Checks

**GET /api/health**:
- Database connectivity
- Redis connectivity
- Returns 200 (healthy) or 503 (unhealthy)

**Kubernetes** (future):
- Liveness: `/api/health`
- Readiness: `/api/health` + migrations complete

## Deployment

### Docker Compose (Development)
```bash
docker compose -f deploy/compose.yml up --build
```

**Services**:
- `postgres`: Database
- `redis`: Cache
- `api`: FastAPI backend
- `web`: Next.js frontend

### Production (Future)

**Kubernetes**:
- API: Deployment with 3+ replicas
- Web: Deployment with 2+ replicas
- Postgres: StatefulSet or managed service
- Redis: StatefulSet or managed service

**CI/CD**:
- GitHub Actions
- Build → Test → Push images → Deploy

## Testing Strategy

### Unit Tests
- Provider normalization
- Dedupe algorithm
- Ranking formulas
- Amenity extraction

### Integration Tests
- Full agent pipeline
- Database operations
- Cache operations

### Contract Tests
- Provider schema stability
- API response schemas

### E2E Tests (Playwright)
- Search flow
- Multi-entity search
- Follow-up refinement
- Personalization toggle

### Performance Tests (Future)
- Load testing with Locust
- Provider latency monitoring

## Future Enhancements

### Phase 2
- [ ] Real-time hours data
- [ ] Photo integration
- [ ] Review sentiment analysis
- [ ] Mobile apps (React Native)

### Phase 3
- [ ] GraphQL API
- [ ] Webhooks for saved searches
- [ ] Machine learning ranking
- [ ] Collaborative filtering

### Phase 4
- [ ] Multi-language support
- [ ] Voice search
- [ ] AR place discovery
- [ ] Social features

## Troubleshooting

### Common Issues

**"No results found"**:
- Check API keys in `.env`
- Verify provider quotas
- Check logs for provider errors

**"Cache hit rate low"**:
- Queries too diverse
- TTL too short
- Check Redis connectivity

**"Slow searches"**:
- Check provider latency in debug.timings
- Consider increasing cache TTL
- Review agent mode (deterministic faster)

### Debug Mode

Set `LOG_LEVEL=DEBUG` to enable verbose logging:
- Provider raw responses
- Dedupe clusters
- Ranking calculations
- Cache keys

## Glossary

- **Anchor**: Primary entity in multi-entity search (e.g., restaurant)
- **Evidence**: Score component breakdown for explainability
- **Fusion**: Combining results from multiple providers
- **Must-Have**: Required amenity in entity specification
- **Partner**: Secondary entity related to anchor (e.g., nearby park)
- **Provenance**: Source attribution for fused places
- **Result Set**: Cached search results for follow-up queries

---

**Last Updated**: 2024-01-15
**Version**: 1.0.0