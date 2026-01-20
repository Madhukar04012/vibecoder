#!/usr/bin/env python
"""
VibeCober CLI - Generate projects from the command line
Usage: 
  python cli.py "Your project idea"              # Preview only
  python cli.py "Your project idea" --build      # Create real files
"""

import sys
import argparse

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

from backend.core.orchestrator import run_agents
from backend.generator.project_builder import build_project


def main():
    parser = argparse.ArgumentParser(
        description="VibeCober - AI Project Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py "Build a SaaS task management app"
  python cli.py "E-commerce platform" --build
  python cli.py "Blog with auth" --build --output ./my-project
        """
    )
    parser.add_argument("idea", help="Your project idea")
    parser.add_argument("--build", action="store_true", help="Create real files on disk")
    parser.add_argument("--output", default="./output", help="Output directory (default: ./output)")
    
    args = parser.parse_args()
    
    print(f"\n>>> VibeCober generating project for:")
    print(f"    \"{args.idea}\"\n")
    print("=" * 50)
    
    # Run the agent pipeline
    result = run_agents(args.idea)
    
    # Display architecture
    print("\n[ARCHITECTURE]")
    arch = result["architecture"]
    print(f"   Project Type: {arch['project_type']}")
    print(f"   Backend: {arch['backend']}")
    print(f"   Frontend: {arch['frontend']}")
    print(f"   Database: {arch['database']}")
    print(f"   Modules: {', '.join(arch['modules'])}")
    
    # Display project structure
    print("\n[PROJECT STRUCTURE]")
    print_structure(result["project_structure"], indent=3)
    
    # Build if requested
    if args.build:
        print("\n" + "=" * 50)
        print("\n[BUILDING PROJECT...]")
        
        build_result = build_project(result["project_structure"], args.output)
        
        print(f"\n   Output: {build_result['output_dir']}")
        print(f"   Folders created: {build_result['total_dirs']}")
        print(f"   Files created: {build_result['total_files']}")
        
        print("\n[FILES CREATED]")
        for f in build_result['created_files']:
            print(f"   + {f}")
        
        print("\n" + "=" * 50)
        print("[SUCCESS] Project built! Open in VS Code:")
        print(f"   code {build_result['output_dir']}")
    else:
        print("\n" + "=" * 50)
        print("[PREVIEW MODE] No files created.")
        print("Run with --build to create real files:")
        print(f"   python cli.py \"{args.idea}\" --build")
    
    return result


def print_structure(structure, indent=0):
    """Recursively print folder/file structure"""
    for name, content in structure.items():
        if isinstance(content, dict):
            print(" " * indent + f"[DIR] {name}/")
            print_structure(content, indent + 3)
        else:
            print(" " * indent + f"[FILE] {name}")


if __name__ == "__main__":
    main()
