"""
VibeCober Full Flow Test Script
Tests: Auth → Project → Plan → Approval → Tasks → Agents → Logs
"""
import requests

API_BASE = "http://127.0.0.1:8000"

def test_full_flow():
    print("=" * 60)
    print("VibeCober Full Flow Test")
    print("=" * 60)

    test_email = "testuser@vibecober.com"
    test_password = "password123"

    # 1. Signup (or login if user exists) - self-contained test
    print("\n[1] Creating/locating user...")
    r = requests.post(f"{API_BASE}/auth/register", json={
        "email": test_email,
        "password": test_password,
        "name": "Test User"
    })
    if r.status_code in (200, 201):
        print(f"    [OK] User registered")
    elif r.status_code == 400 and "already registered" in r.text.lower():
        print(f"    [OK] User exists, will login")
    else:
        print(f"    [INFO] Signup: {r.status_code}, trying login...")

    r = requests.post(f"{API_BASE}/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    if r.status_code != 200:
        print(f"Login failed: {r.status_code} {r.text}")
        return

    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"    [OK] Got token")
    
    # 2. Create Project
    print("\n[2] Creating project...")
    r = requests.post(f"{API_BASE}/projects/", json={
        "idea": "Build a SaaS task management app"
    }, headers=headers)
    
    if r.status_code != 200:
        print(f"Project creation failed: {r.status_code} {r.text}")
        return
    
    project = r.json()
    project_id = project["id"]
    print(f"    [OK] Project created: {project_id[:8]}...")
    
    # 3. Start conversation with Team Lead
    print("\n[3] Talking to Team Lead...")
    r = requests.post(f"{API_BASE}/team-lead/{project_id}/start", json={
        "idea": "Build a SaaS task management app with users, projects, and tasks"
    }, headers=headers)
    
    if r.status_code != 200:
        print(f"Team Lead failed: {r.status_code} {r.text}")
    else:
        response = r.json()
        print(f"    [OK] Response type: {response.get('type', 'unknown')}")
    
    # 4. Approve Plan
    print("\n[4] Approving plan...")
    r = requests.post(f"{API_BASE}/team-lead/{project_id}/approve", json={
        "approved": True
    }, headers=headers)
    
    if r.status_code != 200:
        print(f"Approval failed: {r.status_code} {r.text}")
    else:
        result = r.json()
        print(f"    [OK] Status: {result.get('status', 'unknown')}")
        print(f"    [OK] Tasks created: {result.get('tasks_created', 0)}")
    
    # 5. List Tasks
    print("\n[5] Listing tasks...")
    r = requests.get(f"{API_BASE}/tasks/projects/{project_id}", headers=headers)
    
    if r.status_code != 200:
        print(f"List tasks failed: {r.status_code}")
    else:
        tasks = r.json()
        print(f"    [OK] Found {len(tasks)} tasks")
        for t in tasks[:5]:
            agent = t.get('assigned_agent', 'none')
            status = t.get('status', 'unknown')
            print(f"        - [{agent}] {t['title']} ({status})")
    
    # 6. Run Backend Agent
    print("\n[6] Running Backend Agent...")
    r = requests.post(f"{API_BASE}/agents/backend/{project_id}/run", headers=headers)
    
    if r.status_code != 200:
        print(f"Backend Agent failed: {r.status_code} {r.text}")
    else:
        result = r.json()["result"]
        print(f"    [OK] Status: {result.get('status', 'unknown')}")
        if result.get('task_title'):
            print(f"    [OK] Task: {result['task_title']}")
    
    # 7. Run Frontend Agent
    print("\n[7] Running Frontend Agent...")
    r = requests.post(f"{API_BASE}/agents/frontend/{project_id}/run", headers=headers)
    
    if r.status_code != 200:
        print(f"Frontend Agent failed: {r.status_code} {r.text}")
    else:
        result = r.json()["result"]
        print(f"    [OK] Status: {result.get('status', 'unknown')}")
        if result.get('task_title'):
            print(f"    [OK] Task: {result['task_title']}")
    
    # 8. Check Logs
    print("\n[8] Checking execution logs...")
    r = requests.get(f"{API_BASE}/logs/projects/{project_id}/summary", headers=headers)
    
    if r.status_code != 200:
        print(f"Logs failed: {r.status_code}")
    else:
        summary = r.json()
        print(f"    [OK] Total executions: {summary['total_executions']}")
        print(f"    [OK] Success: {summary['success_count']}")
        print(f"    [OK] Failed: {summary['failure_count']}")
        print(f"    [OK] Files created: {summary['total_files_created']}")
    
    print("\n" + "=" * 60)
    print("[COMPLETE] Full flow test finished!")
    print("=" * 60)
    print(f"\nProject ID for CLI: {project_id}")
    print(f"Token for CLI: {token[:30]}...")

if __name__ == "__main__":
    test_full_flow()
