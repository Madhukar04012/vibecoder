"""
Project Builder - Creates real folders and files on disk
Takes the project structure dict and writes it to the filesystem
"""

import os
from pathlib import Path
from typing import Dict, Any


def _path_to_nested(path: str, content: str) -> dict:
    """Convert 'auth/security.py' -> {'auth': {'security.py': content}}"""
    parts = path.replace("\\", "/").split("/")
    result = {parts[-1]: content}
    for part in reversed(parts[:-1]):
        result = {part: result}
    return result


def _deep_merge(base: dict, overlay: dict) -> dict:
    """Recursively merge overlay into base. Overlay wins on conflicts."""
    result = dict(base)
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def merge_agent_outputs(
    coder_output: dict,
    agent_outputs: Dict[str, Any],
        ) -> dict:
    """
    Merge auth, tester, deployer outputs into coder structure.
    Auth files go into backend/auth/, tests into tests/, deploy at root.
    """
    # Coder output: {project_name: {backend: {...}, frontend: {...}, ...}}
    if not coder_output:
        return {}

    project_name = list(coder_output.keys())[0] if coder_output else "my_project"
    structure = dict(coder_output)

    # Auth files: auth/security.py -> backend/auth/security.py
    auth = agent_outputs.get("auth", {})
    auth_files = auth.get("auth", {}).get("files", {}) or auth.get("files", {})
    for path, content in auth_files.items():
        nested = _path_to_nested(path, content)
        inner = structure.get(project_name, {})
        backend = inner.get("backend", {})
        backend = _deep_merge(backend, nested)
        inner["backend"] = backend
        structure[project_name] = inner

    # Test files: tests/conftest.py
    tester = agent_outputs.get("tester", {})
    test_files = tester.get("tests", {}).get("files", {}) or tester.get("files", {})
    for path, content in test_files.items():
        nested = _path_to_nested(path, content)
        inner = structure.get(project_name, {})
        inner = _deep_merge(inner, nested)
        structure[project_name] = inner

    # Deploy files: Dockerfile, docker-compose.yml at root
    deploy = agent_outputs.get("deployer", {}) or agent_outputs.get("deploy", {})
    deploy_data = deploy.get("deploy", deploy)
    deploy_files = deploy_data.get("files", {})
    for path, content in deploy_files.items():
        nested = _path_to_nested(path, content)
        inner = structure.get(project_name, {})
        inner = _deep_merge(inner, nested)
        structure[project_name] = inner

    return structure


def build_project(structure: dict, output_dir: str = "./output"):
    """
    Takes a nested dict structure and creates real folders/files.
    
    Args:
        structure: Nested dict where keys are folder/file names
                   and values are either dicts (folders) or strings (file content)
        output_dir: Base directory to create the project in
    
    Returns:
        dict with created paths and status
    """
    created_files = []
    created_dirs = []
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    def create_recursive(current_structure: dict, current_path: Path):
        for name, content in current_structure.items():
            item_path = current_path / name
            
            if isinstance(content, dict):
                # It's a folder
                item_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(item_path))
                create_recursive(content, item_path)
            else:
                # It's a file
                item_path.parent.mkdir(parents=True, exist_ok=True)
                item_path.write_text(content, encoding='utf-8')
                created_files.append(str(item_path))
    
    create_recursive(structure, output_path)
    
    return {
        "output_dir": str(output_path.absolute()),
        "created_dirs": created_dirs,
        "created_files": created_files,
        "total_dirs": len(created_dirs),
        "total_files": len(created_files)
    }
