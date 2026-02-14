# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

VibeCober is an AI-powered project generator with a multi-agent architecture that transforms ideas into production-ready code. It uses a Team Lead Brain to orchestrate various specialized agents that handle different aspects of software development.

## Architecture

### Core Components

1. **Backend** (`backend/`) - FastAPI application with modular architecture:
   - `main.py` - Entry point with all API routes
   - `api/` - HTTP routers for different functionalities
   - `agents/` - Specialized AI agents (Planner, DB Schema, Auth, Coder, etc.)
   - `core/` - Orchestrator and agent registry
   - `engine/` - Advanced features like atoms engine, sandbox, circuit breaker
   - `models/` - SQLAlchemy database models
   - `schemas/` - Pydantic data schemas

2. **Frontend** (`frontend/`) - React + TypeScript application:
   - Vite-based build system
   - Monaco editor integration
   - TailwindCSS styling
   - Zustand for state management

3. **CLI** (`cli.py`) - Command-line interface for project generation and agent execution

### Agent Pipeline

The system uses a deterministic agent pipeline orchestrated by the Team Lead Brain:

1. **Team Lead Brain** - Decides which agents to run based on project idea and mode
2. **Orchestrator** - Executes agents in the correct order with proper dependencies
3. **Specialized Agents**:
   - Planner: Architecture decisions and tech stack
   - DB Schema: Database design and models
   - Auth: Authentication system (JWT)
   - Coder: Project structure and code generation
   - Tester: Test suite generation
   - Deployer: Docker and deployment configuration
   - Code Reviewer: Quality assurance

## Common Development Commands

### Backend Development

```bash
# Start the backend API server
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# Run backend tests
pytest backend/tests/

# Check database and create default user
python check_db.py

# Install backend dependencies
pip install -r backend/requirements.txt
```

### Frontend Development

```bash
# Install frontend dependencies
cd frontend && npm install

# Start frontend development server
cd frontend && npm run dev

# Build frontend for production
cd frontend && npm run build

# Run frontend tests
cd frontend && npm test
```

### CLI Usage

```bash
# Generate a project (preview mode)
python cli.py generate "blog with authentication"

# Generate and build project files
python cli.py generate "SaaS with payments" --production --build

# Run backend agent on a project
python cli.py run backend <project_id>

# Run frontend agent on a project
python cli.py run frontend <project_id>

# Run all agents
python cli.py run all <project_id>

# View execution logs
python cli.py logs <project_id>
```

### Database Management

```bash
# Run database migrations
cd backend && alembic upgrade head

# Create new migration
cd backend && alembic revision --autogenerate -m "migration message"
```

## Testing

### Backend Tests

Tests are located in `backend/tests/` and use pytest:

```bash
# Run all tests
cd backend && pytest

# Run specific test file
cd backend && pytest tests/test_circuit_breaker.py

# Run with coverage
cd backend && pytest --cov=.
```

### Frontend Tests

Frontend tests use Vitest:

```bash
# Run all frontend tests
cd frontend && npm test

# Run tests in watch mode
cd frontend && npm run test:watch
```

## Project Generation Modes

1. **Simple** (`--simple`) - Minimal output (planner + coder only)
2. **Full** (`--full`) - Standard generation with DB and auth
3. **Production** (`--production`) - Full stack with tests and deployment config

## Key Features

- **Deterministic Output** - Templates ensure consistent, predictable results
- **Multi-Agent Architecture** - Specialized agents handle different concerns
- **Docker Integration** - Automatic Dockerfile and docker-compose generation
- **Test Generation** - Pytest suites generated automatically
- **Authentication Ready** - Built-in JWT authentication system
- **Extensible Design** - Easy to add new agents without changing orchestrator

## Entry Points

- **Backend**: `backend/main.py`
- **Frontend**: `frontend/src/main.tsx`
- **CLI**: `cli.py`

## Development Workflow

1. Make changes to backend/frontend code
2. Run tests to ensure functionality
3. Test with CLI commands to verify agent behavior
4. Check generated output quality
5. Update documentation if needed

## Environment Setup

1. Copy `.env.example` to `.env` and configure variables
2. Install backend dependencies: `pip install -r backend/requirements.txt`
3. Install frontend dependencies: `cd frontend && npm install`
4. Run database setup: `python check_db.py`
5. Start backend: `uvicorn backend.main:app --reload`
6. Start frontend: `cd frontend && npm run dev`