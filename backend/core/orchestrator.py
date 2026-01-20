from backend.agents.planner import planner_agent
from backend.agents.coder import code_agent

def run_agents(user_idea: str):
    architecture = planner_agent(user_idea)
    project_structure = code_agent(architecture)

    return {
        "input_idea": user_idea,
        "architecture": architecture,
        "project_structure": project_structure
    }
