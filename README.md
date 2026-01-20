# 🚀 VibeCober

**AI-powered project generator** that turns an idea into a real, runnable codebase in seconds.

> Local AI. Zero API cost. Production-ready templates.

---

## 🧠 What is VibeCober?

VibeCober is an **AI-powered project generator** that takes a simple idea like:

> "Build a SaaS task management app"

…and automatically:

- 🧠 **Analyzes** the idea using local AI
- 🏗️ **Decides** architecture, tech stack, and modules
- 📁 **Generates** a complete project structure
- 💾 **Creates** real files on disk
- ▶️ **Produces** a runnable backend & frontend

**This is not a code snippet generator.**
**This is a real project scaffolding engine.**

---

## ❓ Why VibeCober?

Most AI tools today:
- ❌ Output text or JSON
- ❌ Break during setup
- ❌ Depend on expensive cloud APIs
- ❌ Are demos, not foundations

**VibeCober is different.**

### 🔥 What makes it special

| Feature | VibeCober |
|---------|-----------|
| Real runnable code | ✅ (not just text) |
| Local AI | ✅ Ollama + Mistral (free, private, fast) |
| Multi-agent architecture | ✅ |
| Safe fallback system | ✅ (never breaks) |
| CLI-first experience | ✅ |
| Production templates | ✅ |

---

## 🧩 How It Works

VibeCober uses a **multi-agent pipeline**:

```
User Idea
   ↓
Planner Agent (AI-powered)
   ↓
Coder Agent (structure & templates)
   ↓
Project Builder (writes files to disk)
```

- **AI decides** what to build
- **Templates decide** how it's built

This keeps output clean, safe, and reliable.

---

## 🏗️ Architecture Overview

```
vibecober/
├── cli.py                          # CLI entry point
├── backend/
│   ├── main.py                     # FastAPI app
│   ├── api/generate.py             # /generate/project endpoint
│   ├── agents/
│   │   ├── planner.py              # AI-powered planner
│   │   └── coder.py                # Structure generator
│   ├── core/
│   │   ├── orchestrator.py         # Agent pipeline
│   │   └── llm_client.py           # Ollama interface
│   ├── generator/
│   │   └── project_builder.py      # File system writer
│   └── templates/
│       └── code_templates.py       # Professional starter code
```

---

## 🚀 Quick Start

### 1️⃣ Clone the repository

```bash
git clone https://github.com/your-username/vibecober.git
cd vibecober
```

### 2️⃣ Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 3️⃣ Install Ollama + Mistral (for AI)

```bash
# Install Ollama from https://ollama.com/download
ollama pull mistral
```

### 4️⃣ Run the API (optional)

```bash
uvicorn backend.main:app --reload
```

Open:
- 👉 http://127.0.0.1:8000
- 👉 http://127.0.0.1:8000/docs

### 5️⃣ Generate a project via CLI

**Preview** (no files created):
```bash
python cli.py "Build a SaaS task management app"
```

**Build real files**:
```bash
python cli.py "Build a SaaS task management app" --build
```

**Custom output directory**:
```bash
python cli.py "E-commerce platform" --build --output ./my-projects
```

---

## ▶️ Run the Generated Project

### Backend

```bash
cd output/my_project/backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Endpoints:
- `GET /` → status
- `GET /api/health` → health check

### Frontend

```bash
cd output/my_project/frontend
npm install
npm run dev
```

---

## ⚠️ Windows Users (Important)

If `npm install` fails due to PowerShell policy, run **once**:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then retry:
```bash
npm install
npm run dev
```

> This is a system setting, not a VibeCober bug.

---

## 🤖 AI Integration

| Setting | Value |
|---------|-------|
| AI Runtime | Ollama (local) |
| Model | Mistral 7B |
| Cost | ₹0 (no cloud APIs) |
| Privacy | 100% local |

If AI fails or returns invalid output →
✅ VibeCober automatically falls back to a safe default architecture.

---

## 📊 Example AI Outputs

| Input Idea | Generated Modules |
|------------|-------------------|
| E-commerce with payments | auth, products, cart, checkout, orders, admin, payments |
| SaaS project management | auth, user_management, teams, billing |
| Healthcare booking | auth, appointments, doctors, patients |
| Task management app | tasks, assignments, tracking, notifications |

---

## 🆚 Comparison

| Feature | Typical AI Tools | VibeCober |
|---------|------------------|-----------|
| Output | Text / JSON | Real runnable code |
| Backend | ❌ | FastAPI + CORS |
| Frontend | ❌ | React + Vite |
| Styling | ❌ | Dark theme UI |
| AI | Cloud APIs | Local (free) |
| Reliability | Often breaks | Safe fallback |
| CLI Tool | ❌ | ✅ |
| File Generation | ❌ | ✅ |

---

## 🧪 Test Status

| Component | Status |
|-----------|--------|
| API | ✅ |
| CLI Preview | ✅ |
| CLI Build | ✅ |
| File Creation | ✅ |
| Generated Backend | ✅ |
| Health Endpoints | ✅ |
| AI Planner | ✅ |
| Fallback System | ✅ |

---

## 🛣️ Roadmap

- [ ] v0.2: More agents (DB schema, routes, tests)
- [ ] Web UI for non-CLI users
- [ ] Project customization flags
- [ ] Plugin system
- [ ] Team & enterprise features

---

## 🏁 Final Note

**VibeCober is not a tutorial project.**

It is a:
- ✅ Production-ready foundation
- ✅ Multi-agent AI system
- ✅ Local, reliable, extensible platform

If you're building developer tools,
**this is where the future starts.**

---

## 📄 License

MIT License - feel free to use, modify, and distribute.

---

**Built with 🔥 by the VibeCober team**