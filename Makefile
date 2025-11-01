.PHONY: help dev up down build test lint clean seed install-api install-web

help:
	@echo "Available targets:"
	@echo "  dev          - Start development environment"
	@echo "  up           - Start all services with docker-compose"
	@echo "  down         - Stop all services"
	@echo "  build        - Build docker images"
	@echo "  test         - Run all tests"
	@echo "  lint         - Run linters"
	@echo "  clean        - Clean temporary files"
	@echo "  seed         - Seed database with sample data"
	@echo "  install-api  - Install API dependencies"
	@echo "  install-web  - Install web dependencies"

install-api:
	cd apps/api && pip install -e ".[dev]"

install-web:
	cd apps/web && npm install

dev: up
	@echo "Development environment started"
	@echo "API: http://localhost:8000/docs"
	@echo "Web: http://localhost:3000"

up:
	docker compose -f deploy/compose.yml up --build

down:
	docker compose -f deploy/compose.yml down

build:
	docker compose -f deploy/compose.yml build

test:
	cd apps/api && pytest -v
	cd apps/web && npm run test:e2e

lint:
	cd apps/api && ruff check . && black --check . && isort --check-only .
	cd apps/web && npm run lint

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .next -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

seed:
	docker compose -f deploy/compose.yml exec api python -m app.db.seed