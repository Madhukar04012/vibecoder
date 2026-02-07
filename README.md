# VibeCober 🚀

## AI-Powered Project Generator with Multi-Agent Architecture

Transform ideas into production-ready code using an intelligent agent pipeline.

```bash
python cli.py generate "SaaS blog with authentication" --production --build
```

---

## ✨ What VibeCober Does

VibeCober is an **agentic software factory** that generates complete backend projects from a single idea:

| What You Say | What You Get |
| ------------ | ------------ |
| "Build a todo app" | SQLAlchemy models, FastAPI routes, tests |
| "SaaS with auth and payments" | Full auth system, JWT, database schema, Docker config |
| "API for a blog" | CRUD endpoints, user management, pytest suite |

**One command. Production-ready output.**

---

## 🧠 The Brain Behind It

VibeCober uses a **Team Lead Brain** to decide which agents run:

```text
User Idea
    ↓
Team Lead Brain (decides agents)
    ↓
Orchestrator (executes plan)
    ↓
Generated Project
```

### Agent Stack

| Agent | Purpose | Output |
| ----- | ------- | ------ |
| **Team Lead Brain** | Decides execution plan | JSON agent list |
| **Planner** | Architecture decisions | Tech stack, modules |
| **DB Schema** | Database design | SQLAlchemy models |
| **Auth** | Authentication system | JWT, routes, security |
| **Coder** | Project structure | Files and folders |
| **Tester** | Test generation | pytest suite |
| **Deployer** | Deployment config | Docker, compose, Makefile |

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 1b. Install Frontend (Primary UI)

```bash
cd frontend
npm install
```

### 2. Generate a Project

```bash
# Simple prototype
python cli.py generate "todo app" --simple

# Full development
python cli.py generate "blog with auth" --full --build

# Production-ready
python cli.py generate "SaaS with payments" --production --build
```

### 3. Run Generated Project

```bash
cd output/
docker-compose up --build
```

---

## 🖥️ Run VibeCober (API + Primary Frontend)

```bash
# Terminal 1 (API)
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 (Landing page)
cd frontend
npm run dev

# IDE UI (Next.js)
# npm run dev:ide
```

Notes:

- The default helper script `start-frontend.bat` starts `frontend`.

---

## 📋 CLI Usage

```bash
python cli.py generate "your idea" [options]
```

### Mode Flags

| Flag | Description | Agents Used |
| ---- | ----------- | ----------- |
| `--simple` | Minimal output | Planner, Coder |
| `--full` | Standard generation (default) | Planner, DB, Auth, Coder |
| `--production` | Full stack with tests & deploy | All 7 agents |

### Additional Flags

| Flag | Description |
| ---- | ----------- |
| `--build` | Write files to disk |
| `--output ./path` | Custom output directory |
| `--skip-tests` | Skip test generation |
| `--no-docker` | Skip Docker files |
| `--v1` | Use legacy pipeline |

### Examples

```bash
# Quick prototype
python cli.py generate "weather app" --simple

# Blog with auth (no Docker)
python cli.py generate "blog with users" --full --no-docker --build

# Production SaaS
python cli.py generate "SaaS invoicing app with auth" --production --build --output ./my-saas
```

---

## 🎯 Example Output

**Command:**

```bash
python cli.py generate "blog with authentication and comments" --production
```

**Output:**

```text
>>> VibeCober generating project
    Idea: "blog with authentication and comments"
    Mode: PRODUCTION
    Pipeline: v2 (Team Lead Brain)
============================================================

[EXECUTION PLAN]
   Project Type: crud
   Complexity: medium
   Agents: planner, db_schema, auth, coder, tester, deployer

[ARCHITECTURE]
   Backend: FastAPI
   Frontend: React
   Database: PostgreSQL
   Modules: authentication, users, posts, comments

[DATABASE SCHEMA]
   Tables: 3
     - users (7 columns)
     - posts (7 columns)
     - comments (6 columns)

[AUTHENTICATION]
   Strategy: jwt
   Routes: register, login, me
   Files: 5

[TESTS]
   Framework: pytest
   Test suites: health, auth
   Files: 4

[DEPLOYMENT]
   Strategy: Docker
   Files: 8

[PROJECT STRUCTURE]
   [DIR] backend/
      [DIR] app/
         [FILE] main.py
         [FILE] database.py
         [DIR] models/
         [DIR] routes/
         [DIR] auth/
      [DIR] tests/
   [FILE] Dockerfile
   [FILE] docker-compose.yml
   [FILE] requirements.txt
```

---

## 📁 Generated Project Structure

```text
output/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI application
│   │   ├── database.py       # SQLAlchemy setup
│   │   ├── models/           # SQLAlchemy models
│   │   ├── routes/           # API endpoints
│   │   └── auth/
│   │       ├── security.py   # Password hashing, JWT
│   │       ├── dependencies.py # get_current_user
│   │       └── routes.py     # /register, /login, /me
│   └── tests/
│       ├── conftest.py       # Fixtures
│       ├── test_auth.py      # Auth tests
│       └── test_health.py    # Health tests
├── Dockerfile
├── Dockerfile.dev
├── docker-compose.yml
├── docker-compose.prod.yml
├── Makefile
├── requirements.txt
├── .env.production
└── DEPLOY.md
```

---

## 🐳 Running with Docker

```bash
cd output/

# Development (with hot reload)
docker-compose up --build

# Production
docker-compose -f docker-compose.prod.yml up -d --build

# Run tests
docker-compose run --rm api pytest
```

**Useful Makefile commands:**

```bash
make dev      # Start development
make prod     # Start production
make test     # Run tests
make logs     # View logs
make clean    # Clean up
```

---

## 🧪 Running Tests

```bash
cd output/

# Run all tests
pytest

# With verbose output
pytest -v

# Specific test file
pytest tests/test_auth.py
```

---

## 🔧 Architecture

### Why This Design?

VibeCober follows a **deterministic agent pipeline**:

1. **No AI Hallucination Risk** - Templates, not generated text
2. **Predictable Output** - Same input = same output
3. **Production Focus** - Real code, not demos
4. **Extensible** - Add agents without touching orchestrator

### MetaGPT vs VibeCober

| Aspect | MetaGPT | VibeCober |
| ------ | ------: | --------- |
| Focus | Research | Production |
| Output | Varied | Deterministic |
| Auth | Optional | Built-in |
| Tests | Optional | Built-in |
| Docker | No | Yes |
| Complexity | High | Controlled |

---

## 📊 Version

**v0.3.0** - Agentic Architecture Complete

- ✅ Team Lead Brain
- ✅ 7-Agent Pipeline
- ✅ CLI with Mode Flags
- ✅ Docker Deployment
- ✅ Test Generation

---

## 🗺️ Roadmap

- [ ] Frontend Agent (React/Vue generation)
- [ ] Alembic Migrations
- [ ] CI/CD Templates
- [ ] Web UI Dashboard
- [ ] Plugin System

---

## 📄 License

MIT License - Use freely, build boldly.

---

**Built with discipline. Designed for developers.**
