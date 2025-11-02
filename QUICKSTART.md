# Around Me - Quickstart Guide

Get up and running with Around Me in under 5 minutes!

## Prerequisites

- Docker & Docker Compose installed
- API keys for:
  - [Google Places API v1](https://developers.google.com/maps/documentation/places/web-service/get-api-key)
  - [Yelp Fusion API](https://www.yelp.com/developers/documentation/v3/authentication)
  - [OpenAI API](https://platform.openai.com/api-keys)

## Step 1: Clone and Configure
```bash
# Clone the repository
git clone <repo-url>
cd aroundme

# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your favorite editor
```

**Required in `.env`:**
```bash
GOOGLE_PLACES_API_KEY=your_google_key_here
YELP_API_KEY=your_yelp_key_here
OPENAI_API_KEY=your_openai_key_here
```

## Step 2: Start Services
```bash
# Build and start all services
docker compose -f deploy/compose.yml up --build

# Or use make
make up
```

Wait for services to start (~2 minutes first time):
- ✅ Postgres initialization
- ✅ Redis startup
- ✅ API migrations
- ✅ Web build

## Step 3: Access the Application

Open your browser:
- **Web UI**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## Step 4: Try Your First Search

### Via Web UI

1. Go to http://localhost:3000
2. Enter a query: `coffee`
3. Confirm location (or use current location)
4. Click **Search**
5. View results on map or list!

### Via API
```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "coffee",
    "lat": 32.814,
    "lng": -96.948,
    "radius_m": 3000,
    "top_k": 10
  }'
```

## Common Tasks

### Stop Services
```bash
docker compose -f deploy/compose.yml down

# Or
make down
```

### View Logs
```bash
# All services
docker compose -f deploy/compose.yml logs -f

# Specific service
docker compose -f deploy/compose.yml logs -f api
docker compose -f deploy/compose.yml logs -f web
```

### Seed Database
```bash
docker compose -f deploy/compose.yml exec api python -m app.db.seed
```

### Run Tests
```bash
# API tests
cd apps/api
pytest -v

# Web E2E tests
cd apps/web
npm run test:e2e
```

### Reset Everything
```bash
docker compose -f deploy/compose.yml down -v
docker compose -f deploy/compose.yml up --build
```

## Example Queries

### Simple Search
```json
{
  "query": "italian restaurant",
  "lat": 32.814,
  "lng": -96.948,
  "radius_m": 5000
}
```

### With Filters
```json
{
  "query": "coffee",
  "lat": 32.814,
  "lng": -96.948,
  "radius_m": 3000,
  "filters": {
    "price": [1, 3],
    "open_now": true
  }
}
```

### Multi-Entity Query
```json
{
  "query": "family-friendly restaurant near park with playground",
  "lat": 32.814,
  "lng": -96.948,
  "radius_m": 3000,
  "multi_entity": {
    "entities": [
      {
        "kind": "restaurant",
        "must_haves": ["family_friendly", "changing_station"]
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
    "top_k": 30
  }
}
```

## Development Mode

For active development without Docker:

### Backend
```bash
cd apps/api

# Install dependencies
pip install -e ".[dev]"

# Set up database
alembic upgrade head

# Run server
uvicorn app.main:app --reload

# API available at http://localhost:8000
```

### Frontend
```bash
cd apps/web

# Install dependencies
npm install

# Run dev server
npm run dev

# Web available at http://localhost:3000
```

## Troubleshooting

### "Connection refused" errors

**Issue**: Services not ready yet

**Solution**: Wait 30 seconds and try again, or check logs:
```bash
docker compose -f deploy/compose.yml logs
```

### "Invalid API key" errors

**Issue**: API keys not configured correctly

**Solution**: 
1. Check `.env` file has correct keys
2. Restart services: `docker compose down && docker compose up`
3. Verify keys at provider dashboards

### "No results found"

**Issue**: Query too specific or provider quotas exceeded

**Solution**:
1. Try broader query
2. Check provider quotas
3. View debug info in response
4. Check logs: `docker compose logs api`

### Database errors

**Issue**: Migrations not run

**Solution**:
```bash
docker compose exec api alembic upgrade head
```

### Cache issues

**Issue**: Stale data

**Solution**:
```bash
docker compose exec redis redis-cli FLUSHALL
```

## Next Steps

- 📖 Read the [Architecture Guide](docs/ARCHITECTURE.md)
- 🧪 Run the [test suite](CONTRIBUTING.md#testing)
- 🎨 Customize the [frontend](apps/web/)
- 🤖 Explore [agent nodes](apps/api/app/agent/)
- 🔧 Configure [ranking presets](docs/ARCHITECTURE.md#ranking-system)
- 📊 Set up [monitoring](apps/web/app/admin/page.tsx)

## Getting Help

- 📝 [Full Documentation](README.md)
- 🐛 [Report Issues](https://github.com/yourusername/aroundme/issues)
- 💬 [Discussions](https://github.com/yourusername/aroundme/discussions)
- 📧 Email: support@aroundme.example.com

## Quick Reference

| Service | URL | Purpose |
|---------|-----|---------|
| Web UI | http://localhost:3000 | User interface |
| API | http://localhost:8000 | Backend API |
| API Docs | http://localhost:8000/docs | Interactive API docs |
| Health | http://localhost:8000/api/health | Health check |
| Admin | http://localhost:3000/admin | Monitoring dashboard |

**Default Credentials**: None (no auth required for demo)

---

Happy discovering! 🎉