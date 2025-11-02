# Around Me - Local Discovery Agent

An AI-powered local discovery platform that helps users find places with advanced agentic reasoning, multi-entity search, and personalized recommendations.

## Features

### Core Capabilities
- 🤖 **Agentic AI Search** - LangGraph-powered agent interprets natural language queries
- 🔍 **Multi-Provider Fusion** - Combines Google Places v1 and Yelp Fusion APIs
- 🎯 **Smart Ranking** - Evidence-based scoring with explainability
- 🔗 **Multi-Entity Queries** - Find places near other places (e.g., "restaurant near park with playground")
- 💬 **Conversational Follow-ups** - Refine searches across multiple turns
- ⚡ **Personalization** - Opt-in preference learning with bounded boosts
- 📊 **Full Provenance** - Track data sources and deduplication decisions

### Technical Features
- **Deduplication** - RapidFuzz + Haversine clustering across providers
- **Caching** - Redis-based result caching with 15-min conversation context
- **Rate Limiting** - slowapi-based protection
- **Observability** - Structured logging with trace IDs and timing breakdowns
- **Testing** - Unit, integration, contract, and E2E tests

## Tech Stack

### Backend
- Python 3.11, FastAPI, Uvicorn
- LangGraph for agentic workflows
- SQLAlchemy 2.x + Alembic (Postgres)
- Redis for caching
- Google Places API v1 & Yelp Fusion

### Frontend
- Next.js 14 (App Router)
- TypeScript, TailwindCSS, shadcn/ui
- React Query, Leaflet maps
- Playwright for E2E testing

### Infrastructure
- Docker & docker-compose
- GitHub Actions CI
- Postgres 15, Redis 7

## Quick Start

### Prerequisites
- Docker & Docker Compose
- API Keys:
  - [Google Places API v1](https://developers.google.com/maps/documentation/places/web-service/get-api-key)
  - [Yelp Fusion API](https://www.yelp.com/developers/documentation/v3/authentication)
  - [OpenAI API](https://platform.openai.com/api-keys) (for LLM-powered agent)

### Setup

1. **Clone the repository**
```bash
git clone <repo-url>
cd aroundme
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

3. **Start services**
```bash
docker compose -f deploy/compose.yml up --build
```

4. **Access the application**
- **Web UI**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

### Development Setup

**API (Backend)**
```bash
cd apps/api
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

**Web (Frontend)**
```bash
cd apps/web
npm install
npm run dev
```

## Usage Examples

### Simple Query
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

### Multi-Entity Query
```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

### Follow-up Refinement
```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "which have wifi",
    "lat": 32.814,
    "lng": -96.948,
    "radius_m": 3000,
    "context": {
      "conversation_id": "conv-123",
      "result_set_id": "result-456",
      "follow_up": true
    }
  }'
```

## Project Structure
```
.
├── apps/
│   ├── api/              # FastAPI backend
│   │   ├── app/
│   │   │   ├── agent/    # LangGraph nodes and tools
│   │   │   ├── providers/# Google Places & Yelp clients
│   │   │   ├── fusion/   # Dedupe & ranking logic
│   │   │   ├── routes/   # API endpoints
│   │   │   └── db/       # SQLAlchemy models
│   │   └── tests/        # Unit & integration tests
│   └── web/              # Next.js frontend
│       ├── app/          # App router pages
│       ├── components/   # React components
│       └── lib/          # API client & utilities
├── deploy/
│   └── compose.yml       # Docker Compose config
├── docs/
│   └── ARCHITECTURE.md   # Detailed architecture docs
└── README.md
```

## Key Concepts

### Ranking System
Places are scored using a weighted combination of:
- **Rating** (0-5 scale): 55% weight
- **Reviews** (logarithmic): 30% weight
- **Distance** (inverse): 15% weight
- **Bonuses**: open_now, price_fit, preferences (max +0.15)

**Presets**:
- `balanced`: Default weights
- `nearby`: Prioritizes distance (45% weight)
- `review-heavy`: Prioritizes reviews (50% weight)

### Multi-Entity Constraints
Define complex spatial queries:
```json
{
  "entities": [
    {"kind": "restaurant", "must_haves": ["changing_station"]},
    {"kind": "park", "must_haves": ["playground"]}
  ],
  "relations": [
    {"left": 0, "right": 1, "relation": "NEAR", "distance_m": 500}
  ]
}
```

### Personalization
Opt-in preference storage:
- Preferences stored in Postgres
- Bounded boost (max +0.15 total)
- Full CRUD via `/api/profile/preferences`

## Testing

### Backend Tests
```bash
cd apps/api
pytest -v                      # Unit & integration tests
pytest --cov=app              # With coverage
```

### Frontend Tests
```bash
cd apps/web
npm run lint                   # ESLint
npm run test:e2e              # Playwright E2E tests
```

### Manual Testing
Use the provided Postman collection or curl commands above.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_PLACES_API_KEY` | Google Places API key | Required |
| `YELP_API_KEY` | Yelp Fusion API key | Required |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `AGENT_MODE` | Agent mode: `full` or `deterministic` | `full` |
| `RANKING_PRESET` | Default ranking preset | `balanced` |
| `PERSONALIZATION_DEFAULT` | Default personalization state | `off` |
| `RATE_LIMIT_PER_MINUTE` | API rate limit | `60` |
| `CACHE_TTL_SECONDS` | Cache TTL | `1200` |

See `.env.example` for full list.

## API Documentation

Interactive API docs available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation including:
- Agent graph flow
- Provider contracts
- Fusion & deduplication algorithms
- Ranking formulas
- Multi-entity constraint resolution
- Caching strategy
- Database schema

## Contributing

### Code Style
- **Python**: Black, isort, ruff
- **TypeScript**: ESLint, Prettier
- **Commits**: Conventional Commits

### Running Checks
```bash
make lint                      # Run all linters
make test                      # Run all tests
```

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Google Maps Platform for Places API
- Yelp for Fusion API
- LangChain/LangGraph for agent framework
- OpenStreetMap for map tiles

## Support

- **Issues**: GitHub Issues
- **Docs**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **API Docs**: http://localhost:8000/docs

---

Built with ❤️ using FastAPI, Next.js, and LangGraph