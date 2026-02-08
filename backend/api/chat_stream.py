"""
AI Code Generation Streaming API — Live Code Writing
Cursor/Bolt-style: AI writes code character-by-character in the editor.
Multi-agent pipeline: TeamLead → Planner → Coder → Writer
"""

import asyncio
import json
import os
import re
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatStreamRequest(BaseModel):
    prompt: str = ""
    files: dict = Field(default_factory=dict)


# ─── Templates ───────────────────────────────────────────────────────────────

TEMPLATES = {
    "react": {
        "package.json": '{\n  "name": "my-app",\n  "private": true,\n  "version": "1.0.0",\n  "type": "module",\n  "scripts": {\n    "dev": "vite",\n    "build": "vite build",\n    "preview": "vite preview"\n  },\n  "dependencies": {\n    "react": "^18.3.1",\n    "react-dom": "^18.3.1"\n  },\n  "devDependencies": {\n    "@vitejs/plugin-react": "^4.3.0",\n    "vite": "^5.4.0"\n  }\n}',
        "vite.config.js": 'import { defineConfig } from "vite";\nimport react from "@vitejs/plugin-react";\n\nexport default defineConfig({\n  plugins: [react()],\n});',
        "index.html": '<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8" />\n  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n  <title>My App</title>\n</head>\n<body>\n  <div id="root"></div>\n  <script type="module" src="/src/main.jsx"></script>\n</body>\n</html>',
        "src/main.jsx": 'import React from "react";\nimport ReactDOM from "react-dom/client";\nimport App from "./App";\nimport "./index.css";\n\nReactDOM.createRoot(document.getElementById("root")).render(\n  <React.StrictMode>\n    <App />\n  </React.StrictMode>\n);',
        "src/index.css": '* {\n  margin: 0;\n  padding: 0;\n  box-sizing: border-box;\n}\n\nbody {\n  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;\n  -webkit-font-smoothing: antialiased;\n  background: #0f0f0f;\n  color: #e5e5e5;\n  min-height: 100vh;\n}',
        "src/App.jsx": 'import { useState } from "react";\n\nexport default function App() {\n  const [count, setCount] = useState(0);\n\n  return (\n    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "100vh", gap: "1rem" }}>\n      <h1 style={{ fontSize: "2rem", fontWeight: "bold" }}>My App</h1>\n      <p>Count: {count}</p>\n      <button\n        onClick={() => setCount(c => c + 1)}\n        style={{ padding: "0.5rem 1.5rem", borderRadius: "0.5rem", border: "none", background: "#2563eb", color: "white", cursor: "pointer", fontSize: "1rem" }}\n      >\n        Increment\n      </button>\n    </div>\n  );\n}',
    },
    "nextjs": {
        "package.json": '{\n  "name": "my-nextjs-app",\n  "version": "1.0.0",\n  "private": true,\n  "scripts": {\n    "dev": "next dev",\n    "build": "next build",\n    "start": "next start"\n  },\n  "dependencies": {\n    "next": "^14.0.0",\n    "react": "^18.3.1",\n    "react-dom": "^18.3.1"\n  }\n}',
        "app/layout.tsx": 'import type { Metadata } from "next";\n\nexport const metadata: Metadata = {\n  title: "My App",\n  description: "Built with Next.js",\n};\n\nexport default function RootLayout({ children }: { children: React.ReactNode }) {\n  return (\n    <html lang="en">\n      <body>{children}</body>\n    </html>\n  );\n}',
        "app/page.tsx": 'export default function Home() {\n  return (\n    <main style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>\n      <h1>Welcome to My App</h1>\n      <p>Built with Next.js</p>\n    </main>\n  );\n}',
        "app/globals.css": '* { margin: 0; padding: 0; box-sizing: border-box; }\nbody { font-family: system-ui, sans-serif; }',
        "next.config.js": '/** @type {import("next").NextConfig} */\nconst nextConfig = {};\nmodule.exports = nextConfig;',
    },
    "python_api": {
        "main.py": 'from fastapi import FastAPI\nfrom fastapi.middleware.cors import CORSMiddleware\nfrom routes import router\n\napp = FastAPI(title="My API", version="1.0.0")\n\napp.add_middleware(\n    CORSMiddleware,\n    allow_origins=["*"],\n    allow_methods=["*"],\n    allow_headers=["*"],\n)\n\napp.include_router(router)\n\n@app.get("/")\ndef root():\n    return {"message": "API is running", "version": "1.0.0"}\n',
        "routes.py": 'from fastapi import APIRouter\n\nrouter = APIRouter(prefix="/api")\n\n@router.get("/health")\ndef health():\n    return {"status": "healthy"}\n\n@router.get("/items")\ndef get_items():\n    return [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]\n',
        "models.py": 'from pydantic import BaseModel\nfrom typing import Optional\n\nclass Item(BaseModel):\n    id: Optional[int] = None\n    name: str\n    description: str = ""\n    price: float = 0.0\n',
        "requirements.txt": "fastapi==0.109.0\nuvicorn==0.24.0\npydantic==2.5.0\n",
    },
    "fullstack": {
        "backend/main.py": 'from fastapi import FastAPI\nfrom fastapi.middleware.cors import CORSMiddleware\nfrom backend.routes import router\n\napp = FastAPI(title="Full-Stack App")\napp.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])\napp.include_router(router, prefix="/api")\n\n@app.get("/")\ndef root():\n    return {"message": "API running"}\n',
        "backend/routes.py": 'from fastapi import APIRouter\n\nrouter = APIRouter()\n\n@router.get("/health")\ndef health():\n    return {"status": "ok"}\n',
        "backend/models.py": 'from pydantic import BaseModel\n\nclass User(BaseModel):\n    id: int\n    name: str\n    email: str\n',
        "backend/requirements.txt": "fastapi\nuvicorn\npydantic\n",
        "frontend/index.html": '<!DOCTYPE html>\n<html lang="en">\n<head><meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" /><title>App</title></head>\n<body><div id="root"></div><script type="module" src="/src/main.jsx"></script></body>\n</html>',
        "frontend/package.json": '{\n  "name": "frontend",\n  "private": true,\n  "scripts": { "dev": "vite", "build": "vite build" },\n  "dependencies": { "react": "^18.3.1", "react-dom": "^18.3.1" },\n  "devDependencies": { "@vitejs/plugin-react": "^4.3.0", "vite": "^5.4.0" }\n}',
        "frontend/src/main.jsx": 'import React from "react";\nimport ReactDOM from "react-dom/client";\nimport App from "./App";\n\nReactDOM.createRoot(document.getElementById("root")).render(<React.StrictMode><App /></React.StrictMode>);',
        "frontend/src/App.jsx": 'import { useState, useEffect } from "react";\n\nexport default function App() {\n  const [data, setData] = useState(null);\n  useEffect(() => {\n    fetch("/api/health").then(r => r.json()).then(setData);\n  }, []);\n  return <div style={{padding:"2rem"}}><h1>Full-Stack App</h1><pre>{JSON.stringify(data, null, 2)}</pre></div>;\n}',
        "README.md": "# Full-Stack App\n\n## Backend\ncd backend && pip install -r requirements.txt && uvicorn main:app --reload\n\n## Frontend\ncd frontend && npm install && npm run dev\n",
    },
}

# ─── LLM Helpers ─────────────────────────────────────────────────────────────

def _detect_project_type(prompt: str) -> str:
    p = prompt.lower()
    if any(w in p for w in ["next.js", "nextjs", "next js"]):
        return "nextjs"
    if any(w in p for w in ["python", "fastapi", "flask", "django", "api only", "backend only"]):
        return "python_api"
    if any(w in p for w in ["full stack", "fullstack", "full-stack"]):
        return "fullstack"
    return "react"


def _call_nim_for_code(prompt: str, file_path: str, project_context: str = "") -> str | None:
    import requests
    api_key = os.getenv("NIM_API_KEY", "").strip()
    if not api_key:
        return None
    ext = file_path.rsplit(".", 1)[-1] if "." in file_path else ""
    lang = {"py": "Python", "ts": "TypeScript", "tsx": "TypeScript React", "js": "JavaScript",
            "jsx": "JavaScript React", "json": "JSON", "css": "CSS", "html": "HTML"}.get(ext, "code")
    system_msg = f"""You are an expert software engineer. Generate the COMPLETE contents of the file '{file_path}' ({lang}).
Rules:
- Write production-ready, clean code
- NO markdown, NO explanations, NO code fences
- Output ONLY the raw file content
- Include all imports, exports, and logic
- Follow best practices for {lang}"""
    if project_context:
        system_msg += f"\n\nProject context:\n{project_context}"
    model = os.getenv("NIM_MODEL", "meta/llama-3.3-70b-instruct")
    try:
        r = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": f"User request: {prompt}\n\nGenerate the complete file: {file_path}"},
            ], "max_tokens": 2048, "temperature": 0.3},
            timeout=60,
        )
        r.raise_for_status()
        content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        content = re.sub(r'^```\w*\n?', '', content.strip())
        content = re.sub(r'\n?```$', '', content.strip())
        return content.strip() if content.strip() else None
    except Exception as e:
        print(f"[NIM] Code gen error for {file_path}: {e}")
        return None


def _call_nim_chat(prompt: str, context: str = "") -> str | None:
    import requests
    api_key = os.getenv("NIM_API_KEY", "").strip()
    if not api_key:
        return None
    model = os.getenv("NIM_MODEL", "meta/llama-3.3-70b-instruct")
    system_msg = "You are a helpful AI coding assistant in an IDE. Be concise and helpful."
    if context:
        system_msg += f"\n\nCurrent project files:\n{context}"
    try:
        r = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt},
            ], "max_tokens": 512, "temperature": 0.5},
            timeout=30,
        )
        r.raise_for_status()
        return r.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip() or None
    except Exception:
        return None


def _call_ollama_chat(prompt: str) -> str | None:
    import requests
    model = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2")
    try:
        r = requests.post("http://localhost:11434/api/generate",
                          json={"model": model, "prompt": prompt, "stream": False}, timeout=30)
        r.raise_for_status()
        return r.json().get("response", "").strip() or None
    except Exception:
        return None


def _is_code_request(prompt: str) -> bool:
    p = prompt.lower().strip()
    triggers = [
        "create", "build", "make", "generate", "scaffold", "setup", "start",
        "new project", "todo app", "chat app", "landing page", "dashboard",
        "website", "web app", "api", "crud", "blog", "portfolio",
        "e-commerce", "ecommerce", "calculator", "game", "clone",
        "authentication", "login", "signup", "register",
        "add a", "add an", "implement", "write",
    ]
    return any(t in p for t in triggers)


# ─── Live Code Writing Speed ─────────────────────────────────────────────────
# Characters per chunk for live typing effect (higher = faster)
TYPING_CHARS_PER_CHUNK = 8
TYPING_DELAY_MS = 0.008  # delay between chunks in seconds


# ─── Stream Generator with Live Code Writing ─────────────────────────────────

async def stream_generator(prompt: str, existing_files: dict) -> AsyncGenerator[str, None]:
    """
    SSE stream with multi-agent pipeline and live code writing.

    Events:
      - agent_start:   An agent step is beginning (name, description)
      - agent_end:     An agent step completed
      - thinking:      AI is processing
      - message:       Chat text from AI (full)
      - message_token: Streamed chat character
      - file_start:    Starting to write a file (creates empty file in IDE)
      - file_delta:    Characters being typed into the file (LIVE WRITING)
      - file_end:      File writing complete
      - done:          All done
      - error:         Something went wrong
    """
    def event(etype: str, data: dict) -> str:
        return f"data: {json.dumps({'type': etype, **data})}\n\n"

    try:
        is_code = _is_code_request(prompt)

        if is_code:
            # ═══════════════════════════════════════════════════════════
            #  MULTI-AGENT PIPELINE WITH LIVE CODE WRITING
            # ═══════════════════════════════════════════════════════════

            # ── Agent 1: Team Lead ────────────────────────────────────
            yield event("agent_start", {
                "agent": "team_lead",
                "name": "Team Lead",
                "icon": "brain",
                "description": "Analyzing requirements...",
            })
            await asyncio.sleep(0.3)

            project_type = _detect_project_type(prompt)
            template = TEMPLATES.get(project_type, TEMPLATES["react"])
            file_list = list(template.keys())

            yield event("agent_end", {
                "agent": "team_lead",
                "result": f"Identified {project_type.replace('_', ' ')} project with {len(file_list)} files",
            })
            await asyncio.sleep(0.15)

            # ── Agent 2: Planner ──────────────────────────────────────
            yield event("agent_start", {
                "agent": "planner",
                "name": "Planner",
                "icon": "map",
                "description": "Designing project architecture...",
            })
            await asyncio.sleep(0.2)

            # Build context from existing files
            ctx_parts = [f"- {p}" for p in list(existing_files.keys())[:10]]
            project_context = "\n".join(ctx_parts) if ctx_parts else ""

            plan_text = f"Creating {project_type.replace('_', ' ')} project: {', '.join(file_list)}"
            yield event("agent_end", {
                "agent": "planner",
                "result": plan_text,
            })
            await asyncio.sleep(0.15)

            # ── Agent 3: Coder — generates and LIVE-WRITES each file ─
            yield event("agent_start", {
                "agent": "coder",
                "name": "Engineer",
                "icon": "code",
                "description": "Writing code...",
            })
            await asyncio.sleep(0.1)

            yield event("message", {
                "content": f"Building your {project_type.replace('_', ' ')} project. Watch the code appear live in the editor...",
            })
            await asyncio.sleep(0.1)

            total = len(template)
            idx = 0

            for file_path, default_content in template.items():
                idx += 1

                # ── file_start: creates the file (empty) in the IDE ──
                yield event("file_start", {
                    "path": file_path,
                    "index": idx,
                    "total": total,
                })
                await asyncio.sleep(0.05)

                # ── Generate code (AI or template) ──
                content = _call_nim_for_code(prompt, file_path, project_context)
                if not content:
                    content = default_content

                # ── LIVE WRITING: stream character chunks into editor ─
                pos = 0
                chunk_size = TYPING_CHARS_PER_CHUNK
                while pos < len(content):
                    chunk = content[pos:pos + chunk_size]
                    yield event("file_delta", {
                        "path": file_path,
                        "delta": chunk,
                    })
                    pos += chunk_size
                    await asyncio.sleep(TYPING_DELAY_MS)

                # ── file_end: mark file complete ─────────────────────
                yield event("file_end", {
                    "path": file_path,
                    "index": idx,
                    "total": total,
                })
                await asyncio.sleep(0.05)

            yield event("agent_end", {
                "agent": "coder",
                "result": f"Wrote {total} files",
            })
            await asyncio.sleep(0.1)

            yield event("message", {
                "content": f"Done! Created {total} files. Your project is ready.",
            })

        else:
            # ═══════════════════════════════════════════════════════════
            #  CHAT MODE — no files, just conversation
            # ═══════════════════════════════════════════════════════════
            yield event("thinking", {"message": "Thinking..."})
            await asyncio.sleep(0.3)

            file_list_str = ", ".join(list(existing_files.keys())[:20]) if existing_files else "none"
            reply = _call_nim_chat(prompt, f"Files: {file_list_str}")
            if not reply:
                reply = _call_ollama_chat(prompt)
            if not reply:
                reply = f'I can help with that! Try asking me to "create a todo app" or "build a landing page".'

            for i in range(0, len(reply), 3):
                yield event("message_token", {"token": reply[i:i + 3]})
                await asyncio.sleep(0.02)

            yield event("message", {"content": reply})

        yield event("done", {"message": "Complete"})

    except Exception as e:
        yield event("error", {"message": str(e)})
        yield event("done", {"message": "Complete"})


@router.post("/stream")
async def chat_stream(body: ChatStreamRequest):
    return StreamingResponse(
        stream_generator(body.prompt, body.files),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
