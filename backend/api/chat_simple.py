from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ChatRequest(BaseModel):
    prompt: str


BUILD_KEYWORDS = [
    "create the project",
    "start project",
    "full stack project",
    "fsd project",
]


def is_build_intent(prompt: str) -> bool:
    p = prompt.lower()
    return any(k in p for k in BUILD_KEYWORDS)


@router.post("/chat")
def chat(req: ChatRequest):
    prompt = req.prompt.strip()

    # 🔥 HARD ACTION MODE
    if is_build_intent(prompt):
        return {
            "reply": "Project created",
            "files": [
                {
                    "path": "backend/requirements.txt",
                    "content": "fastapi\nuvicorn\n",
                },
                {
                    "path": "backend/app/__init__.py",
                    "content": "",
                },
                {
                    "path": "backend/app/routes.py",
                    "content": "from fastapi import APIRouter\n\nrouter = APIRouter()\n\n@router.get('/ping')\ndef ping():\n    return {'status': 'ok'}\n",
                },
                {
                    "path": "backend/app/services.py",
                    "content": "def get_status():\n    return 'ok'\n",
                },
                {
                    "path": "frontend/index.html",
                    "content": "<!doctype html><div id='app'></div>",
                },
                {
                    "path": "frontend/package.json",
                    "content": "{\n  \"name\": \"frontend\",\n  \"private\": true\n}\n",
                },
                {
                    "path": "frontend/src/main.js",
                    "content": "console.log('app loaded');\n",
                },
                {
                    "path": "frontend/src/styles.css",
                    "content": "body { margin: 0; font-family: sans-serif; }\n",
                },
                {
                    "path": ".env",
                    "content": "",
                },
                {
                    "path": "README.md",
                    "content": "# Full-Stack Project\n",
                },
                {
                    "path": "backend/main.py",
                    "content": "from fastapi import FastAPI\nfrom backend.app.routes import router\n\napp = FastAPI()\napp.include_router(router)\n",
                },
            ],
        }

    # 💬 Chat-only fallback
    return {
        "reply": prompt,
        "files": [],
    }
