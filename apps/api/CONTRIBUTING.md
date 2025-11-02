# Contributing to Around Me

Thank you for your interest in contributing to Around Me! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Git

### Setup Development Environment

1. **Fork and clone the repository**
```bash
git clone https://github.com/yourusername/aroundme.git
cd aroundme
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Install dependencies**
```bash
# API
cd apps/api
pip install -e ".[dev]"

# Web
cd ../web
npm install
```

4. **Run database migrations**
```bash
cd apps/api
alembic upgrade head
```

5. **Start development servers**
```bash
# Terminal 1 - API
cd apps/api
uvicorn app.main:app --reload

# Terminal 2 - Web
cd apps/web
npm run dev
```

## Development Workflow

### Branching Strategy

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(api): add multi-entity constraint join
fix(web): correct map marker clustering
docs: update architecture diagram
test(api): add dedupe algorithm tests
```

### Code Style

#### Python (API)
- Follow PEP 8
- Use Black for formatting (line length: 100)
- Use isort for import sorting
- Use ruff for linting
- Run pre-commit hooks:
```bash
cd apps/api
pre-commit install
pre-commit run --all-files
```

#### TypeScript (Web)
- Follow ESLint rules
- Use Prettier for formatting
- Run linter:
```bash
cd apps/web
npm run lint
```

### Testing

#### Backend Tests
```bash
cd apps/api

# Run all tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_dedupe.py -v

# Run specific test
pytest tests/test_dedupe.py::TestDeduplication::test_normalize_name -v
```

#### Frontend Tests
```bash
cd apps/web

# Run E2E tests
npm run test:e2e

# Run in headed mode
npx playwright test --headed

# Run specific test
npx playwright test e2e/search.spec.ts
```

### Adding New Features

1. **Create a feature branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Implement your feature**
   - Write tests first (TDD encouraged)
   - Follow existing code patterns
   - Add documentation

3. **Test your changes**
```bash
make test
make lint
```

4. **Commit your changes**
```bash
git add .
git commit -m "feat(scope): description"
```

5. **Push and create PR**
```bash
git push origin feature/your-feature-name
```

## Pull Request Process

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] No merge conflicts with target branch

### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed

## Checklist
- [ ] Tests pass
- [ ] Linting passes
- [ ] Documentation updated
- [ ] Self-reviewed code
```

### Review Process

1. Automated CI checks must pass
2. At least one maintainer approval required
3. Address review feedback
4. Squash commits if requested
5. Maintainer will merge

## Project Structure
```
aroundme/
├── apps/
│   ├── api/          # FastAPI backend
│   └── web/          # Next.js frontend
├── docs/             # Documentation
├── deploy/           # Deployment configs
└── packages/         # Shared packages
```

### Key Files

- **API Entry**: `apps/api/app/main.py`
- **Agent Logic**: `apps/api/app/agent/`
- **Web Pages**: `apps/web/app/`
- **Components**: `apps/web/components/`

## Adding New Providers

To add a new place provider:

1. **Create provider class**
```python
# apps/api/app/providers/newprovider.py
from app.providers.base import BaseProvider

class NewProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "newprovider"
    
    async def search_nearby(self, ...):
        # Implementation
        pass
```

2. **Add normalization logic**
```python
def _normalize_place(self, data, origin_lat, origin_lng):
    # Map provider schema to ProviderPlace
    return ProviderPlace(...)
```

3. **Update agent tools**
```python
# apps/api/app/agent/tools.py
# Add new provider to SearchTool
```

4. **Add tests**
```python
# apps/api/tests/test_providers.py
class TestNewProvider:
    # Test cases
```

5. **Update documentation**

## Database Migrations

### Creating a Migration
```bash
cd apps/api
alembic revision -m "description of changes"
# Edit the generated file in app/migrations/versions/
alembic upgrade head
```

### Migration Guidelines

- Never edit existing migrations
- Always test migrations both up and down
- Include sample data if needed
- Document schema changes

## Documentation

### Updating Documentation

- API changes: Update OpenAPI schema
- Features: Update README.md
- Architecture: Update docs/ARCHITECTURE.md
- Code: Add docstrings and comments

### Writing Documentation

- Use clear, concise language
- Include code examples
- Add diagrams where helpful
- Keep up-to-date with code changes

## Performance Guidelines

- **API Endpoints**: Target <1.5s response time
- **Database Queries**: Use indexes, avoid N+1
- **Caching**: Cache expensive operations
- **Provider Calls**: Parallel when possible
- **Frontend**: Optimize bundle size, lazy load

## Security Guidelines

- Never commit API keys or secrets
- Validate all user input
- Use parameterized queries
- Follow OWASP guidelines
- Report security issues privately

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Security**: Email security@example.com
- **Chat**: Join our Discord (link TBD)

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone.

### Standards

- Be respectful and inclusive
- Accept constructive criticism
- Focus on what's best for the community
- Show empathy towards others

### Enforcement

Unacceptable behavior may be reported to the project team. All complaints will be reviewed and investigated.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

Thank you for contributing! 🎉