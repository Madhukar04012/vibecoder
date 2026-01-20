"""
Project Builder - Creates real folders and files on disk
Takes the project structure dict and writes it to the filesystem
"""

import os
from pathlib import Path


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
