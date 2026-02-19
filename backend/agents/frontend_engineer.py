"""
Frontend Engineer Agent - Executes frontend-related tasks.

Responsibility:
- Pick next available frontend task
- Execute the task (generate React/Vite code)
- Update task status in DB
- Log execution results

Mirrors BackendEngineerAgent pattern.
"""

from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from backend.models.task import Task
from backend.models.project import Project
from backend.models.project_plan import ProjectPlan
from backend.models.execution_log import ExecutionLog
from backend.models.enums import TaskStatus, AgentRole
from backend.generator.project_builder import build_project
import json


class FrontendEngineerAgent:
    """
    Executes frontend tasks for a project.
    Generates React + Vite code with API integration.
    """

    def __init__(self, db: Session):
        self.db = db
        self.role = AgentRole.FRONTEND_ENGINEER

    def run_next_task(self, project_id: str) -> Dict[str, Any]:
        """
        Find and execute the next available frontend task.
        """
        task = self._get_next_task(project_id)
        
        if not task:
            return {
                "status": "no_tasks",
                "message": "No pending frontend tasks found"
            }
        
        # Mark as in progress
        task.status = TaskStatus.IN_PROGRESS
        self.db.commit()
        
        try:
            # Execute
            result = self._execute_task(project_id, task)
            
            # Mark as done and log success
            task.status = TaskStatus.DONE
            
            log = ExecutionLog(
                task_id=task.id,
                project_id=project_id,
                agent="frontend_engineer",
                status="success",
                message=f"Task '{task.title}' executed successfully",
                files_created=result.get("files_created", 0),
                output_dir=result.get("output_dir", "")
            )
            self.db.add(log)
            self.db.commit()
            
            return {
                "status": "completed",
                "task_id": task.id,
                "task_title": task.title,
                "result": result
            }
            
        except Exception as e:
            # Rollback and log failure
            task.status = TaskStatus.TODO
            
            log = ExecutionLog(
                task_id=task.id,
                project_id=project_id,
                agent="frontend_engineer",
                status="failure",
                message=str(e),
                files_created=0
            )
            self.db.add(log)
            self.db.commit()
            
            return {
                "status": "failed",
                "task_id": task.id,
                "task_title": task.title,
                "error": str(e)
            }

    def _get_next_task(self, project_id: str) -> Optional[Task]:
        """Get next pending frontend task."""
        return (
            self.db.query(Task)
            .filter(
                Task.project_id == project_id,
                Task.assigned_agent == AgentRole.FRONTEND_ENGINEER,
                Task.status == TaskStatus.TODO
            )
            .order_by(Task.priority.desc(), Task.created_at.asc())
            .first()
        )

    def _execute_task(self, project_id: str, task: Task) -> Dict[str, Any]:
        """Execute the task based on title."""
        title = task.title.lower()
        
        if "frontend" in title or "react" in title or "layout" in title:
            return self._generate_frontend_base(project_id)
        elif "auth" in title or "login" in title:
            return self._generate_auth_pages(project_id)
        elif "dashboard" in title or "home" in title:
            return self._generate_dashboard(project_id)
        else:
            return self._generate_placeholder_component(project_id, task.title)

    # ============ FRONTEND GENERATORS ============

    def _generate_frontend_base(self, project_id: str) -> Dict[str, Any]:
        """Generate React + Vite + TypeScript + Tailwind S-class base structure."""
        project_name = f"project_{project_id[:8]}"
        
        # Try S-class templates first
        try:
            from backend.templates.sclass_templates import get_sclass_frontend_templates
            sclass_files = get_sclass_frontend_templates()
            
            # Organize into nested structure
            frontend = {}
            for path, content in sclass_files.items():
                parts = path.replace("\\", "/").split("/")
                current = frontend
                for part in parts[:-1]:
                    current = current.setdefault(part, {})
                current[parts[-1]] = content
            
            structure = {project_name: {"frontend": frontend}}
            result = build_project(structure, f"./generated/{project_id}")
            return {
                "action": "frontend_base_sclass",
                "files_created": result.get("total_files", 0),
                "output_dir": result.get("output_dir", ""),
                "quality": result.get("quality", {}),
            }
        except ImportError:
            pass
        
        # Fallback to legacy templates
        structure = {
            project_name: {
                "frontend": {
                    "package.json": self._package_json_template(),
                    "vite.config.js": self._vite_config_template(),
                    "index.html": self._index_html_template(),
                    "src": {
                        "main.jsx": self._main_jsx_template(),
                        "App.jsx": self._app_jsx_template(),
                        "App.css": self._app_css_template(),
                        "api": {
                            "client.js": self._api_client_template(),
                        },
                        "components": {
                            "Header.jsx": self._header_component_template(),
                        }
                    }
                }
            }
        }
        
        result = build_project(structure, f"./generated/{project_id}")
        return {
            "action": "frontend_base",
            "files_created": result.get("total_files", 0),
            "output_dir": result.get("output_dir", "")
        }

    def _generate_auth_pages(self, project_id: str) -> Dict[str, Any]:
        """Generate S-class login/register pages with TypeScript and Tailwind."""
        project_name = f"project_{project_id[:8]}"
        
        structure = {
            project_name: {
                "frontend": {
                    "src": {
                        "pages": {
                            "Login.tsx": self._login_page_template(),
                            "Register.tsx": self._register_page_template(),
                        },
                        "hooks": {
                            "use-auth.ts": self._use_auth_hook_template(),
                        },
                        "stores": {
                            "auth-store.ts": self._auth_store_template(),
                        },
                    }
                }
            }
        }
        
        result = build_project(structure, f"./generated/{project_id}")
        return {
            "action": "auth_pages",
            "files_created": result.get("total_files", 0),
            "output_dir": result.get("output_dir", "")
        }

    def _generate_dashboard(self, project_id: str) -> Dict[str, Any]:
        """Generate dashboard/home page."""
        project_name = f"project_{project_id[:8]}"
        
        structure = {
            project_name: {
                "frontend": {
                    "src": {
                        "pages": {
                            "Dashboard.jsx": self._dashboard_page_template(),
                        }
                    }
                }
            }
        }
        
        result = build_project(structure, f"./generated/{project_id}")
        return {
            "action": "dashboard",
            "files_created": result.get("total_files", 0),
            "output_dir": result.get("output_dir", "")
        }

    def _generate_placeholder_component(self, project_id: str, task_title: str) -> Dict[str, Any]:
        """Generate an S-class TypeScript component."""
        project_name = f"project_{project_id[:8]}"
        component_name = "".join(word.capitalize() for word in task_title.split()[:3])
        kebab_name = "-".join(word.lower() for word in task_title.split()[:3])
        
        structure = {
            project_name: {
                "frontend": {
                    "src": {
                        "components": {
                            f"{component_name}.tsx": f'''import {{ type HTMLAttributes }} from "react";
import {{ cn }} from "@/lib/utils";

interface {component_name}Props extends HTMLAttributes<HTMLDivElement> {{
  title?: string;
  description?: string;
}}

export default function {component_name}({{
  title = "{task_title}",
  description,
  className,
  ...props
}}: {component_name}Props) {{
  return (
    <section
      className={{cn(
        "rounded-xl border bg-card p-6 shadow-sm transition-colors hover:shadow-md",
        className,
      )}}
      {{...props}}
    >
      <h2 className="text-2xl font-bold tracking-tight mb-2">{{title}}</h2>
      {{description && (
        <p className="text-muted-foreground">{{description}}</p>
      )}}
      <div className="mt-4 space-y-3">
        {{/* {component_name} content */}}
      </div>
    </section>
  );
}}
'''
                        }
                    }
                }
            }
        }
        
        result = build_project(structure, f"./generated/{project_id}")
        return {
            "action": "component",
            "component": component_name,
            "files_created": result.get("total_files", 0),
            "output_dir": result.get("output_dir", "")
        }

    # ============ TEMPLATES ============

    def _package_json_template(self) -> str:
        return '''{
  "name": "vibecober-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0"
  }
}
'''

    def _vite_config_template(self) -> str:
        return '''import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
});
'''

    def _index_html_template(self) -> str:
        return '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>VibeCober App</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
'''

    def _main_jsx_template(self) -> str:
        return '''import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './App.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
'''

    def _app_jsx_template(self) -> str:
        return '''import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Header from './components/Header';

function Home() {
  return (
    <div className="home">
      <h1>Welcome to VibeCober App</h1>
      <p>Your AI-generated full-stack application</p>
    </div>
  );
}

export default function App() {
  return (
    <div className="app">
      <Header />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
      </main>
    </div>
  );
}
'''

    def _app_css_template(self) -> str:
        return '''* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  min-height: 100vh;
  color: #eee;
}

.app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  margin-bottom: 30px;
}

.header h1 {
  font-size: 1.5rem;
  background: linear-gradient(90deg, #00d4ff, #7b2cbf);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.header nav a {
  color: #aaa;
  text-decoration: none;
  margin-left: 20px;
  transition: color 0.2s;
}

.header nav a:hover {
  color: #00d4ff;
}

.home {
  text-align: center;
  padding: 60px 20px;
}

.home h1 {
  font-size: 3rem;
  margin-bottom: 20px;
}

.home p {
  color: #888;
  font-size: 1.2rem;
}

button {
  background: linear-gradient(90deg, #00d4ff, #7b2cbf);
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
}

button:hover {
  transform: scale(1.05);
}

input {
  width: 100%;
  padding: 12px;
  border: 1px solid #333;
  border-radius: 8px;
  background: #1a1a2e;
  color: #eee;
  margin-bottom: 15px;
}

input:focus {
  outline: none;
  border-color: #00d4ff;
}
'''

    def _api_client_template(self) -> str:
        return '''// API Client - Uses Vite proxy for /api routes
const API_BASE = '';

export async function apiCall(endpoint, options = {}) {
  const token = localStorage.getItem('token');
  
  const headers = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
}

export const api = {
  get: (endpoint) => apiCall(endpoint),
  post: (endpoint, data) => apiCall(endpoint, { method: 'POST', body: JSON.stringify(data) }),
  patch: (endpoint, data) => apiCall(endpoint, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (endpoint) => apiCall(endpoint, { method: 'DELETE' }),
};
'''

    def _header_component_template(self) -> str:
        return '''import React from 'react';
import { Link } from 'react-router-dom';

export default function Header() {
  return (
    <header className="header">
      <h1>VibeCober App</h1>
      <nav>
        <Link to="/">Home</Link>
        <Link to="/dashboard">Dashboard</Link>
        <Link to="/login">Login</Link>
      </nav>
    </header>
  );
}
'''

    def _login_page_template(self) -> str:
        return '''import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = await api.post('/auth/login', { email, password });
      localStorage.setItem('token', data.access_token);
      navigate('/dashboard');
    } catch (err) {
      setError('Invalid credentials');
    }
  };

  return (
    <div className="auth-page">
      <h2>Login</h2>
      {error && <p className="error">{error}</p>}
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button type="submit">Login</button>
      </form>
    </div>
  );
}
'''

    def _register_page_template(self) -> str:
        return '''import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';

export default function Register() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/auth/signup', { email, password, name: email.split('@')[0] });
      navigate('/login');
    } catch (err) {
      setError('Registration failed');
    }
  };

  return (
    <div className="auth-page">
      <h2>Register</h2>
      {error && <p className="error">{error}</p>}
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button type="submit">Register</button>
      </form>
    </div>
  );
}
'''

    def _use_auth_hook_template(self) -> str:
        return '''import { useAuthStore } from "@/stores/auth-store";
import { apiClient } from "@/lib/api-client";
import { useCallback } from "react";

export function useAuth() {
  const { user, token, setUser, setToken, logout: clearAuth } = useAuthStore();

  const login = useCallback(async (email: string, password: string) => {
    const response = await apiClient.post<{ token: string; user: { id: string; email: string; name: string } }>(
      "/api/v1/auth/login",
      { email, password },
    );
    setToken(response.token);
    setUser(response.user);
    return response.user;
  }, [setToken, setUser]);

  const register = useCallback(async (name: string, email: string, password: string) => {
    const response = await apiClient.post<{ token: string; user: { id: string; email: string; name: string } }>(
      "/api/v1/auth/register",
      { name, email, password },
    );
    setToken(response.token);
    setUser(response.user);
    return response.user;
  }, [setToken, setUser]);

  const logout = useCallback(() => {
    clearAuth();
  }, [clearAuth]);

  return { user, token, isAuthenticated: !!token, login, register, logout };
}
'''

    def _auth_store_template(self) -> str:
        return '''import { create } from "zustand";
import { persist } from "zustand/middleware";

interface User {
  id: string;
  email: string;
  name: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      setUser: (user) => set({ user }),
      setToken: (token) => set({ token }),
      logout: () => set({ user: null, token: null }),
    }),
    { name: "auth-storage" },
  ),
);
'''

    def _dashboard_page_template(self) -> str:
        return '''import React, { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/health')
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="dashboard">
      <h2>Dashboard</h2>
      <div className="stats">
        <div className="stat-card">
          <h3>API Status</h3>
          <p>{data?.status || 'Unknown'}</p>
        </div>
      </div>
    </div>
  );
}
'''
