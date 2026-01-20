"""
Planner Agent - Decides project architecture
Now powered by AI with safe fallback to hardcoded response
"""

from backend.core.llm_client import call_ollama


# Fallback architecture - used if AI fails
HARDCODED_FALLBACK = {
    "project_type": "Web Application",
    "backend": "FastAPI",
    "frontend": "React",
    "database": "PostgreSQL",
    "modules": ["authentication", "users", "dashboard"]
}


def planner_agent(user_idea: str):
    """
    Takes a user idea and returns architecture decisions.
    Uses AI when available, falls back to hardcoded response if AI fails.
    """
    
    prompt = f'''Output ONLY a JSON object, no other text. Format:
{{"project_type":"Web Application","backend":"FastAPI","frontend":"React","database":"PostgreSQL","modules":["auth","users"]}}

Analyze this idea and output appropriate modules: {user_idea}

JSON:'''

    # Try AI first
    ai_response = call_ollama(prompt)

    if ai_response:
        # Validate response has required keys
        required_keys = HARDCODED_FALLBACK.keys()
        if all(k in ai_response for k in required_keys):
            print("[PLANNER] Using AI-generated architecture")
            return ai_response
        else:
            print("[PLANNER] AI response missing keys, using fallback")

    # Fallback if AI fails
    print("[PLANNER] Using fallback architecture")
    return HARDCODED_FALLBACK
