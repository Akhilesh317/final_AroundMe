"""Setup file for Around Me API"""
from setuptools import find_packages, setup

setup(
    name="aroundme-api",
    version="1.0.0",
    description="Around Me - Local Discovery Agent API",
    author="Around Me Team",
    python_requires=">=3.11",
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "httpx>=0.26.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "sqlalchemy>=2.0.25",
        "alembic>=1.13.0",
        "psycopg[binary]>=3.1.16",
        "redis>=5.0.1",
        "slowapi>=0.1.9",
        "loguru>=0.7.2",
        "structlog>=24.1.0",
        "langgraph>=0.0.20",
        "langchain>=0.1.0",
        "langchain-openai>=0.0.5",
        "openai>=1.10.0",
        "rapidfuzz>=3.6.1",
        "haversine>=2.8.1",
        "python-dotenv>=1.0.0",
        "python-multipart>=0.0.6",
        "numpy>=1.24.0",  # ✅ NEW: For semantic matching embeddings
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.4",
            "pytest-asyncio>=0.23.3",
            "pytest-cov>=4.1.0",
            "httpx>=0.26.0",
            "ruff>=0.1.14",
            "black>=24.1.0",
            "isort>=5.13.2",
            "pre-commit>=3.6.0",
        ]
    },
)