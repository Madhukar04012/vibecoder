"""
Planner Agent - Decides project architecture
Now powered by AI with safe fallback to prompt-aware response
"""


from backend.core.llm_client import nim_chat
from backend.core.tech_detector import detect_stack


def _build_fallback(user_idea: str) -> dict:
    """Build a prompt-aware fallback architecture."""
    stack = detect_stack(user_idea)
    
    result = {
        "project_type": "Web Application",
        "modules": ["core"],
    }
    
    # Backend
    if stack.project_type == "cli":
        result["backend"] = "None"
    elif stack.backend_framework:
        result["backend"] = stack.backend_framework
    elif stack.backend_language == "python":
        result["backend"] = "FastAPI"
    elif stack.backend_language in ("javascript", "typescript"):
        result["backend"] = "Express"
    elif stack.backend_language == "go":
        result["backend"] = "Gin"
    elif stack.backend_language == "java":
        result["backend"] = "Spring Boot"
    elif stack.backend_language == "rust":
        result["backend"] = "Actix"
    elif stack.is_frontend_only:
        result["backend"] = "None"
    else:
        result["backend"] = "FastAPI"  # default
    
    # Frontend
    if stack.project_type in ("cli", "api"):
        result["frontend"] = "None"
    elif stack.frontend_framework:
        result["frontend"] = stack.frontend_framework
    elif stack.is_backend_only:
        result["frontend"] = "None"
    else:
        result["frontend"] = "React"
    
    # Database
    if stack.database:
        result["database"] = stack.database
    else:
        result["database"] = "PostgreSQL"
    
    # Project type
    if stack.project_type == "cli":
        result["project_type"] = "CLI Application"
    elif stack.project_type == "api":
        result["project_type"] = "REST API"
    elif stack.project_type == "mobile":
        result["project_type"] = "Mobile Application"
    elif stack.project_type == "static":
        result["project_type"] = "Static Website"
    elif stack.project_type == "game":
        result["project_type"] = "Game"
    
    # Modules based on features
    idea_lower = user_idea.lower()
    if any(w in idea_lower for w in ["auth", "login", "user"]):
        result["modules"].append("authentication")
    if any(w in idea_lower for w in ["dashboard", "admin"]):
        result["modules"].append("dashboard")
    if any(w in idea_lower for w in ["chat", "message"]):
        result["modules"].append("messaging")
    if any(w in idea_lower for w in ["pay", "stripe", "billing"]):
        result["modules"].append("payments")
    
    return result


def planner_agent(user_idea: str):
    """
    Takes a user idea and returns architecture decisions.
    Uses AI when available, falls back to hardcoded response if AI fails.
    """
    
    prompt = f'''Output ONLY a JSON object, no other text. Format:
{{"project_type":"Web Application","backend":"<framework>","frontend":"<framework or None>","database":"<database>","modules":["module1","module2"]}}

IMPORTANT: Choose the technology stack based on what the user is asking for.
- If they mention Python/Django/Flask/FastAPI, use that for backend
- If they mention Node/Express/NestJS, use that
- If they mention Vue/Angular/Svelte, use that for frontend (NOT always React)
- If they mention Go/Java/Rust, use appropriate frameworks
- Only default to React+FastAPI if no specific tech is mentioned

Analyze this idea and output appropriate tech stack and modules: {user_idea}

JSON:'''

    # Try NIM (DeepSeek V3.2 with reasoning)
    import os
    import json as _json
    import re as _re
    
    nim_key = os.getenv("NIM_API_KEY", "").strip()
    ai_response = None
    
    if nim_key:
        raw = nim_chat(prompt)
        if raw:
            # Extract JSON from AI response
            raw = _re.sub(r'^```\w*\n?', '', raw.strip())
            raw = _re.sub(r'\n?```$', '', raw.strip())
            for pattern in [r'\{[\s\S]*\}']:
                match = _re.search(pattern, raw)
                if match:
                    try:
                        ai_response = _json.loads(match.group())
                        break
                    except _json.JSONDecodeError:
                        continue

    if ai_response:
        # Validate response has required keys
        required_keys = ["project_type", "backend", "frontend", "database", "modules"]
        if all(k in ai_response for k in required_keys):
            print("[PLANNER] Using AI-generated architecture")
            return ai_response
        else:
            print("[PLANNER] AI response missing keys, using fallback")

    # Fallback if AI fails — now prompt-aware
    print("[PLANNER] Using fallback architecture")
    return _build_fallback(user_idea)
