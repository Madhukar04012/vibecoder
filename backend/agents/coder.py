"""
Code Agent - Generates project structure using real templates
"""

from backend.templates.code_templates import get_templates


def code_agent(architecture: dict):
    """
    Takes architecture from planner and returns full project structure
    with real, working starter code.
    """
    # Generate a clean project name from the architecture
    project_name = "my_project"
    
    # Get templates with project-specific values injected
    structure = get_templates(project_name, architecture)
    
    return structure
