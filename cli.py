#!/usr/bin/env python
"""
VibeCober CLI - AI Project Generator & Executor

Commands:
  generate "idea"              Generate a new project
  run backend <project_id>     Run backend engineer agent
"""

import sys
import argparse
import requests

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

# API Configuration
API_BASE = "http://127.0.0.1:8000"
AUTH_TOKEN = None  # Set via login or env var


def main():
    parser = argparse.ArgumentParser(
        description="VibeCober - AI Project Generator & Executor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # ============ GENERATE COMMAND ============
    gen_parser = subparsers.add_parser("generate", help="Generate a new project from idea")
    gen_parser.add_argument("idea", help="Your project idea")
    gen_parser.add_argument("--build", action="store_true", help="Create real files on disk")
    gen_parser.add_argument("--output", default="./output", help="Output directory")
    
    # Phase 2: Mode flags
    mode_group = gen_parser.add_mutually_exclusive_group()
    mode_group.add_argument("--simple", action="store_true", help="Minimal output (planner + coder only)")
    mode_group.add_argument("--full", action="store_true", help="Full generation (default)")
    mode_group.add_argument("--production", action="store_true", help="Production-ready with all agents")
    
    # Phase 2: Skip flags
    gen_parser.add_argument("--skip-tests", action="store_true", help="Skip test generation")
    gen_parser.add_argument("--no-docker", action="store_true", help="Skip Docker/deployment files")
    gen_parser.add_argument("--v1", action="store_true", help="Use legacy v1 pipeline (backward compat)")
    
    # ============ RUN COMMAND ============
    run_parser = subparsers.add_parser("run", help="Run an agent on a project")
    run_subparsers = run_parser.add_subparsers(dest="agent", help="Agent to run")
    
    # run backend
    backend_parser = run_subparsers.add_parser("backend", help="Run backend engineer agent")
    backend_parser.add_argument("project_id", help="Project ID to run agent on")
    backend_parser.add_argument("--all", action="store_true", help="Run all pending backend tasks")
    backend_parser.add_argument("--token", help="Auth token (or set VIBECOBER_TOKEN env var)")
    
    # run frontend
    frontend_parser = run_subparsers.add_parser("frontend", help="Run frontend engineer agent")
    frontend_parser.add_argument("project_id", help="Project ID to run agent on")
    frontend_parser.add_argument("--all", action="store_true", help="Run all pending frontend tasks")
    frontend_parser.add_argument("--token", help="Auth token (or set VIBECOBER_TOKEN env var)")
    
    # run all (backend + frontend)
    all_parser = run_subparsers.add_parser("all", help="Run all agents (backend + frontend)")
    all_parser.add_argument("project_id", help="Project ID to run agents on")
    all_parser.add_argument("--token", help="Auth token (or set VIBECOBER_TOKEN env var)")
    
    # ============ LOGS COMMAND ============
    logs_parser = subparsers.add_parser("logs", help="View execution logs")
    logs_parser.add_argument("project_id", help="Project ID")
    logs_parser.add_argument("--token", help="Auth token")
    
    args = parser.parse_args()
    
    # Route to handlers
    if args.command == "generate":
        handle_generate(args)
    elif args.command == "run" and args.agent == "backend":
        handle_run_backend(args)
    elif args.command == "run" and args.agent == "frontend":
        handle_run_frontend(args)
    elif args.command == "run" and args.agent == "all":
        handle_run_all(args)
    elif args.command == "logs":
        handle_logs(args)
    else:
        parser.print_help()


# ============ GENERATE HANDLER ============
def handle_generate(args):
    """Generate a new project from idea"""
    from backend.core.orchestrator import orchestrate, run_agents
    from backend.generator.project_builder import build_project
    
    # Determine mode
    if args.simple:
        mode = "simple"
    elif args.production:
        mode = "production"
    else:
        mode = "full"
    
    # Use v1 or v2 pipeline
    use_v2 = not getattr(args, 'v1', False)
    
    print(f"\n>>> VibeCober generating project")
    print(f'    Idea: "{args.idea}"')
    print(f"    Mode: {mode.upper()}")
    print(f"    Pipeline: {'v2 (Team Lead Brain)' if use_v2 else 'v1 (Legacy)'}")
    print("=" * 60)
    
    if use_v2:
        # Phase 2: Team Lead Brain
        result = orchestrate(args.idea, mode=mode, use_v2=True)
        
        # Display execution plan
        plan = result.get("execution_plan", {})
        print(f"\n[EXECUTION PLAN]")
        print(f"   Project Type: {plan.get('project_type', 'N/A')}")
        print(f"   Complexity: {plan.get('complexity', 'N/A')}")
        print(f"   Agents: {', '.join(plan.get('agents', []))}")
        
        # Display agent outputs
        outputs = result.get("agent_outputs", {})
        
        if "planner" in outputs:
            arch = outputs["planner"]
            print(f"\n[ARCHITECTURE]")
            print(f"   Backend: {arch.get('backend', 'N/A')}")
            print(f"   Frontend: {arch.get('frontend', 'N/A')}")
            print(f"   Database: {arch.get('database', 'N/A')}")
            print(f"   Modules: {', '.join(arch.get('modules', []))}")
        
        if "db_schema" in outputs:
            db = outputs["db_schema"]
            if db.get("status") == "success":
                tables = db.get("schema", {}).get("tables", [])
                print(f"\n[DATABASE SCHEMA]")
                print(f"   Tables: {len(tables)}")
                for t in tables:
                    print(f"     - {t['name']} ({len(t.get('columns', []))} columns)")
        
        if "auth" in outputs:
            auth = outputs["auth"]
            if auth.get("status") == "success":
                auth_info = auth.get("auth", {})
                print(f"\n[AUTHENTICATION]")
                print(f"   Strategy: {auth_info.get('strategy', 'N/A')}")
                print(f"   Routes: {', '.join(auth_info.get('routes', []))}")
                print(f"   Files: {auth.get('files_count', 0)}")
        
        if "tester" in outputs:
            test = outputs["tester"]
            if test.get("status") == "success":
                print(f"\n[TESTS]")
                print(f"   Framework: pytest")
                print(f"   Test suites: {', '.join(test.get('tests', {}).get('tests', []))}")
                print(f"   Files: {test.get('files_count', 0)}")
        
        if "deployer" in outputs:
            deploy = outputs["deployer"]
            if deploy.get("status") == "success":
                print(f"\n[DEPLOYMENT]")
                print(f"   Strategy: Docker")
                print(f"   Files: {deploy.get('files_count', 0)}")
        
        if "coder" in outputs:
            print(f"\n[PROJECT STRUCTURE]")
            print_structure(outputs["coder"], indent=3)
        
    else:
        # Legacy v1 pipeline
        result = run_agents(args.idea)
        
        print("\n[ARCHITECTURE]")
        arch = result["architecture"]
        print(f"   Project Type: {arch['project_type']}")
        print(f"   Backend: {arch['backend']}")
        print(f"   Frontend: {arch['frontend']}")
        print(f"   Database: {arch['database']}")
        print(f"   Modules: {', '.join(arch['modules'])}")
        
        print("\n[PROJECT STRUCTURE]")
        print_structure(result["project_structure"], indent=3)
    
    # Build if requested
    if args.build:
        print("\n" + "=" * 60)
        print("\n[BUILDING PROJECT...]")
        
        from backend.generator.project_builder import merge_agent_outputs
        
        coder_output = result.get("agent_outputs", {}).get("coder") or result.get("project_structure", {})
        agent_outputs = result.get("agent_outputs", {})
        structure = merge_agent_outputs(coder_output, agent_outputs) if agent_outputs else coder_output
        build_result = build_project(structure, args.output)
        
        print(f"\n   Output: {build_result['output_dir']}")
        print(f"   Folders created: {build_result['total_dirs']}")
        print(f"   Files created: {build_result['total_files']}")
        
        print("\n[FILES CREATED]")
        for f in build_result['created_files']:
            print(f"   + {f}")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Project built!")
    else:
        print("\n" + "=" * 60)
        print("[PREVIEW MODE] No files created.")
        print(f'Run with --build: python cli.py generate "{args.idea}" --build')


# ============ RUN BACKEND HANDLER ============
def handle_run_backend(args):
    """Run backend engineer agent on a project"""
    token = args.token or _get_token()
    
    if not token:
        print("Error: Auth token required. Use --token or set VIBECOBER_TOKEN env var")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    project_id = args.project_id
    
    print(f"\n>>> Running Backend Engineer Agent")
    print(f"    Project: {project_id}")
    print("=" * 50)
    
    if args.all:
        # Run all tasks
        endpoint = f"{API_BASE}/agents/backend/{project_id}/run-all"
        print("\n[MODE] Running ALL pending backend tasks...\n")
    else:
        # Run single task
        endpoint = f"{API_BASE}/agents/backend/{project_id}/run"
        print("\n[MODE] Running next backend task...\n")
    
    try:
        response = requests.post(endpoint, headers=headers, timeout=120)
        
        if response.status_code == 401:
            print("Error: Invalid or expired token")
            return
        elif response.status_code == 404:
            print("Error: Project not found")
            return
        elif response.status_code != 200:
            print(f"Error: API returned {response.status_code}")
            print(response.text)
            return
        
        data = response.json()
        
        if args.all:
            # Multiple results
            _print_run_all_results(data)
        else:
            # Single result
            _print_single_result(data.get("result", {}))
        
        # Show recent logs
        _print_execution_logs(project_id, headers)
        
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to API. Is the server running?")
        print(f"  Start with: uvicorn backend.main:app --reload")
    except Exception as e:
        print(f"Error: {e}")


# ============ RUN FRONTEND HANDLER ============
def handle_run_frontend(args):
    """Run frontend engineer agent on a project"""
    token = args.token or _get_token()
    
    if not token:
        print("Error: Auth token required. Use --token or set VIBECOBER_TOKEN env var")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    project_id = args.project_id
    
    print(f"\n>>> Running Frontend Engineer Agent")
    print(f"    Project: {project_id}")
    print("=" * 50)
    
    if args.all:
        endpoint = f"{API_BASE}/agents/frontend/{project_id}/run-all"
        print("\n[MODE] Running ALL pending frontend tasks...\n")
    else:
        endpoint = f"{API_BASE}/agents/frontend/{project_id}/run"
        print("\n[MODE] Running next frontend task...\n")
    
    try:
        response = requests.post(endpoint, headers=headers, timeout=120)
        
        if response.status_code == 401:
            print("Error: Invalid or expired token")
            return
        elif response.status_code == 404:
            print("Error: Project not found")
            return
        elif response.status_code != 200:
            print(f"Error: API returned {response.status_code}")
            print(response.text)
            return
        
        data = response.json()
        
        if args.all:
            _print_run_all_results(data)
        else:
            _print_single_result(data.get("result", {}))
        
        _print_execution_logs(project_id, headers)
        
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to API. Is the server running?")
        print(f"  Start with: uvicorn backend.main:app --reload")
    except Exception as e:
        print(f"Error: {e}")


# ============ RUN ALL HANDLER ============
def handle_run_all(args):
    """Run all agents (backend + frontend) on a project"""
    token = args.token or _get_token()
    
    if not token:
        print("Error: Auth token required. Use --token or set VIBECOBER_TOKEN env var")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    project_id = args.project_id
    
    print(f"\n>>> Running ALL Agents (Backend + Frontend)")
    print(f"    Project: {project_id}")
    print("=" * 50)
    
    total_completed = 0
    total_failed = 0
    
    # 1. Run Backend Agent
    print("\n[PHASE 1] Backend Engineer Agent")
    print("-" * 40)
    
    try:
        backend_url = f"{API_BASE}/agents/backend/{project_id}/run-all"
        response = requests.post(backend_url, headers=headers, timeout=120)
        
        if response.status_code == 401:
            print("Error: Invalid or expired token")
            return
        elif response.status_code == 404:
            print("Error: Project not found")
            return
        elif response.status_code == 200:
            data = response.json()
            completed = data.get("tasks_completed", 0)
            failed = data.get("tasks_failed", 0)
            total_completed += completed
            total_failed += failed
            
            for r in data.get("results", []):
                status = r.get("status", "unknown")
                title = r.get("task_title", "Unknown")
                if status == "completed":
                    print(f"  [OK] {title}")
                elif status == "failed":
                    print(f"  [FAIL] {title}")
            
            print(f"\nBackend: {completed} completed, {failed} failed")
        else:
            print(f"Error: Backend API returned {response.status_code}")
    except Exception as e:
        print(f"Backend Error: {e}")
    
    # 2. Run Frontend Agent
    print("\n[PHASE 2] Frontend Engineer Agent")
    print("-" * 40)
    
    try:
        frontend_url = f"{API_BASE}/agents/frontend/{project_id}/run-all"
        response = requests.post(frontend_url, headers=headers, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            completed = data.get("tasks_completed", 0)
            failed = data.get("tasks_failed", 0)
            total_completed += completed
            total_failed += failed
            
            for r in data.get("results", []):
                status = r.get("status", "unknown")
                title = r.get("task_title", "Unknown")
                if status == "completed":
                    print(f"  [OK] {title}")
                elif status == "failed":
                    print(f"  [FAIL] {title}")
            
            print(f"\nFrontend: {completed} completed, {failed} failed")
        else:
            print(f"Error: Frontend API returned {response.status_code}")
    except Exception as e:
        print(f"Frontend Error: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"[SUMMARY] Total: {total_completed} completed, {total_failed} failed")
    print(f"\n[OUTPUT] Generated files at: ./generated/{project_id}/")
    
    _print_execution_logs(project_id, headers)


def _print_single_result(result: dict):
    """Print result of single task execution"""
    status = result.get("status", "unknown")
    
    if status == "completed":
        print(f"[OK] Completed: {result.get('task_title', 'Unknown task')}")
        inner = result.get("result", {})
        if inner.get("files_created"):
            print(f"     Files created: {inner['files_created']}")
    elif status == "no_tasks":
        print("[INFO] No pending backend tasks found")
    elif status == "failed":
        print(f"[FAIL] Task: {result.get('task_title', 'Unknown')}")
        print(f"       Error: {result.get('error', 'Unknown error')}")
    else:
        print(f"[?] Status: {status}")


def _print_run_all_results(data: dict):
    """Print results of run-all execution"""
    completed = data.get("tasks_completed", 0)
    failed = data.get("tasks_failed", 0)
    results = data.get("results", [])
    
    for r in results:
        status = r.get("status", "unknown")
        title = r.get("task_title", "Unknown")
        
        if status == "completed":
            print(f"  [OK] {title}")
        elif status == "failed":
            print(f"  [FAIL] {title}")
    
    print("\n" + "-" * 40)
    print(f"Completed: {completed} | Failed: {failed}")


def _print_execution_logs(project_id: str, headers: dict):
    """Fetch and display recent execution logs"""
    try:
        logs_url = f"{API_BASE}/logs/projects/{project_id}"
        response = requests.get(logs_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return
        
        logs = response.json()[:5]  # Show latest 5
        
        if not logs:
            return
        
        print("\n" + "=" * 50)
        print("[RECENT EXECUTION LOGS]")
        
        for log in logs:
            status_icon = "[OK]" if log["status"] == "success" else "[FAIL]"
            agent = log.get("agent", "unknown")
            message = log.get("message", "")[:60]
            files = log.get("files_created", 0)
            
            print(f"  {status_icon} [{agent}] {message}")
            if files:
                print(f"         Files: {files}")
                
    except Exception:
        pass  # Silent fail for logs


# ============ LOGS HANDLER ============
def handle_logs(args):
    """View execution logs for a project"""
    token = args.token or _get_token()
    
    if not token:
        print("Error: Auth token required")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get summary
    summary_url = f"{API_BASE}/logs/projects/{args.project_id}/summary"
    logs_url = f"{API_BASE}/logs/projects/{args.project_id}"
    
    try:
        # Summary
        resp = requests.get(summary_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            s = resp.json()
            print(f"\n>>> Execution Summary for project: {args.project_id}")
            print("=" * 50)
            print(f"  Total executions: {s['total_executions']}")
            print(f"  Success: {s['success_count']}")
            print(f"  Failed: {s['failure_count']}")
            print(f"  Files created: {s['total_files_created']}")
        
        # Detailed logs
        resp = requests.get(logs_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            logs = resp.json()
            print("\n[EXECUTION HISTORY]")
            for log in logs[:10]:
                status = "[OK]" if log["status"] == "success" else "[FAIL]"
                print(f"  {status} {log['message']}")
                
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to API")


# ============ HELPERS ============
def _get_token():
    """Get auth token from environment"""
    import os
    return os.environ.get("VIBECOBER_TOKEN")


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
