"""
Deploy Agent - Generates production-ready deployment configuration

Input: All previous agent outputs
Output: Dockerfile, docker-compose, production configs, README

Deterministic. Production-ready. No AI.
"""

from typing import Dict, Any, List
from pydantic import BaseModel


# ========== TYPES ==========

class DeployOutput(BaseModel):
    strategy: str = "docker"
    includes_compose: bool = True
    requires_env: List[str]
    files: Dict[str, str]


# ========== TEMPLATES ==========

DOCKERFILE_TEMPLATE = '''# VibeCober Generated Dockerfile
# Production-ready Python FastAPI container

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''


DOCKERFILE_DEV_TEMPLATE = '''# VibeCober Generated Dockerfile (Development)
# Hot-reload enabled for development

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

EXPOSE 8000

# Development mode with hot reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
'''


DOCKER_COMPOSE_TEMPLATE = '''# VibeCober Generated docker-compose.yml
# Complete development environment

version: "3.8"

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/app
      - SECRET_KEY=${SECRET_KEY:-your-secret-key-change-this}
      - DEBUG=${DEBUG:-false}
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - .:/app
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=app
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
'''


DOCKER_COMPOSE_PROD_TEMPLATE = '''# VibeCober Generated docker-compose.prod.yml
# Production deployment configuration

version: "3.8"

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=false
    restart: always
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: "0.5"
          memory: 512M

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

volumes:
  postgres_data:
'''


DOCKERIGNORE_TEMPLATE = '''# VibeCober Generated .dockerignore

# Python
__pycache__
*.py[cod]
*$py.class
*.so
.Python
.venv
venv/
ENV/

# Testing
.pytest_cache
.coverage
htmlcov/
tests/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Git
.git
.gitignore

# Docker
Dockerfile*
docker-compose*
.docker

# Misc
*.md
*.log
.env.local
.env.*.local
'''


ENV_PRODUCTION_TEMPLATE = '''# VibeCober Production Environment Variables
# Copy to .env and fill in values

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname
POSTGRES_USER=postgres
POSTGRES_PASSWORD=change-this-password
POSTGRES_DB=app

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production

# App
DEBUG=false
ALLOWED_HOSTS=your-domain.com,api.your-domain.com
'''


MAKEFILE_TEMPLATE = '''# VibeCober Generated Makefile
# Common commands for development and deployment

.PHONY: dev prod build test clean

# Development
dev:
	docker-compose up --build

# Production
prod:
	docker-compose -f docker-compose.prod.yml up -d --build

# Build only
build:
	docker-compose build

# Run tests
test:
	docker-compose run --rm api pytest

# Stop all
stop:
	docker-compose down

# Clean everything
clean:
	docker-compose down -v --rmi local
	find . -type d -name __pycache__ -exec rm -rf {} +

# Logs
logs:
	docker-compose logs -f api

# Shell into container
shell:
	docker-compose exec api bash

# Database migrations (if using alembic)
migrate:
	docker-compose exec api alembic upgrade head
'''


DEPLOY_README_TEMPLATE = '''# Deployment Guide

Auto-generated by VibeCober Deploy Agent.

## Quick Start

### Development

```bash
# Start development environment
docker-compose up --build

# Or use make
make dev
```

API available at: http://localhost:8000
Docs available at: http://localhost:8000/docs

### Production

1. Copy environment file:
```bash
cp .env.production .env
```

2. Edit `.env` with your production values

3. Start production:
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

## Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start development environment |
| `make prod` | Start production environment |
| `make test` | Run test suite |
| `make logs` | View API logs |
| `make stop` | Stop all containers |
| `make clean` | Remove all containers and volumes |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | Yes | JWT signing key (min 32 chars) |
| `DEBUG` | No | Enable debug mode (default: false) |

## Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

## Troubleshooting

### Database connection issues
```bash
docker-compose logs db
```

### API not starting
```bash
docker-compose logs api
```

### Reset everything
```bash
make clean
make dev
```
'''


# ========== DEPLOY AGENT ==========

class DeployAgent:
    """
    Generates deployment configuration.
    Deterministic template-based generation.
    """
    
    def __init__(self, context: Dict[str, Any]):
        self.context = context
        self.mode = context.get("mode", "full")
    
    def generate(self) -> DeployOutput:
        """Generate complete deployment config"""
        files = {
            "Dockerfile": DOCKERFILE_TEMPLATE.strip(),
            "Dockerfile.dev": DOCKERFILE_DEV_TEMPLATE.strip(),
            "docker-compose.yml": DOCKER_COMPOSE_TEMPLATE.strip(),
            "docker-compose.prod.yml": DOCKER_COMPOSE_PROD_TEMPLATE.strip(),
            ".dockerignore": DOCKERIGNORE_TEMPLATE.strip(),
            ".env.production": ENV_PRODUCTION_TEMPLATE.strip(),
            "Makefile": MAKEFILE_TEMPLATE.strip(),
            "DEPLOY.md": DEPLOY_README_TEMPLATE.strip(),
        }
        
        required_env = [
            "DATABASE_URL",
            "SECRET_KEY",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "POSTGRES_DB"
        ]
        
        return DeployOutput(
            strategy="docker",
            includes_compose=True,
            requires_env=required_env,
            files=files
        )


# ========== PUBLIC API ==========

def deploy_agent(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for orchestrator.
    
    Args:
        context: Previous agent outputs
        
    Returns:
        Dict with deployment config and files
    """
    agent = DeployAgent(context)
    output = agent.generate()
    
    return {
        "deploy": output.model_dump(),
        "files_count": len(output.files),
        "status": "success"
    }


# ========== EXAMPLE ==========

if __name__ == "__main__":
    result = deploy_agent({"mode": "production"})
    
    print("=" * 60)
    print("DEPLOY OUTPUT:")
    print("=" * 60)
    print(f"Strategy: {result['deploy']['strategy']}")
    print(f"Files: {list(result['deploy']['files'].keys())}")
    print(f"Required Env: {result['deploy']['requires_env']}")
    
    print("\n" + "=" * 60)
    print("DOCKERFILE:")
    print("=" * 60)
    print(result['deploy']['files']['Dockerfile'][:400] + "...")
