"""
Engineer Agent — Phase-1

Strict-role agent for writing production code.
Runs ONLY in EXECUTION state.
MUST retrieve semantic context before coding.

Usage:
    engineer = EngineerAgent(prd, roadmap)
    files = engineer.execute()
"""

from typing import Dict, Any, List, Optional
import re

from backend.agents.base_agent import BaseAgent


SYSTEM_PROMPT_TEMPLATE = """You are a Senior Software Engineer at a top tech company.
Write the COMPLETE contents of the file '{file_path}'.

CRITICAL RULES:
- Write PRODUCTION-READY, COMPANY-LEVEL code
- NO markdown, NO explanations, NO code fences (```)
- Output ONLY the raw file content — nothing before or after
- Include ALL imports, exports, types, and logic
- Write REAL functionality, not placeholders or TODOs
- Use modern best practices (hooks, functional components, proper CSS)
- For CSS files: write comprehensive styles with variables, responsive design, hover effects
- For components: include proper props, state management, event handlers
- For utils: include real utility functions with error handling
- For package.json: include react, react-dom, @vitejs/plugin-react, vite as dependencies
- For vite.config.js: use @vitejs/plugin-react plugin
- Make it look professional — good spacing, colors, typography

PROJECT CONTEXT:
{project_context}

ADDITIONAL CONTEXT FROM MEMORY:
{memory_context}
"""


class EngineerAgent(BaseAgent):
    """
    Engineer agent for writing production code.
    
    State requirement: EXECUTION
    Input: PRD + Roadmap + Memory Context
    Output: Generated file contents
    """
    
    name = "engineer"
    
    def __init__(self, prd: Dict[str, Any], roadmap: Dict[str, Any]):
        """
        Initialize the engineer with planning context.
        
        Args:
            prd: Product Requirements Document
            roadmap: Architecture and file plan
        """
        super().__init__()
        self.prd = prd
        self.roadmap = roadmap
        self.generated_files: Dict[str, str] = {}
    
    def execute(self) -> Dict[str, str]:
        """
        Generate all files in the roadmap.
        
        Returns:
            Dict mapping file paths to contents
        """
        file_plan = self.roadmap.get("directory_structure", [])
        
        for file_path in file_plan:
            content = self.generate_file(file_path)
            self.generated_files[file_path] = content
        
        return self.generated_files
    
    def generate_file(self, file_path: str, memory_context: str = "") -> str:
        """
        Generate a single file.
        
        Args:
            file_path: Path of the file to generate
            memory_context: Additional context from semantic memory
            
        Returns:
            File content as string
        """
        import json
        
        # Build project context
        project_context = f"""
PRD:
{json.dumps(self.prd, indent=2)}

Architecture:
{json.dumps(self.roadmap, indent=2)}

User request: {self.prd.get('description', self.prd.get('title', 'Build the application'))}
"""
        
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            file_path=file_path,
            project_context=project_context[:3000],  # Limit context size
            memory_context=memory_context[:1000] if memory_context else "No additional context",
        )
        
        response = self.call_llm_simple(
            system=system_prompt,
            user=f"Write the complete file: {file_path}",
            max_tokens=2048,
            temperature=0.3
        )
        
        if not response:
            return self._fallback_content(file_path)
        
        # Clean response (remove markdown fences if present)
        content = re.sub(r'^```\w*\n?', '', response.strip())
        content = re.sub(r'\n?```$', '', content.strip())
        
        return content
    
    def generate_file_with_memory(self, file_path: str) -> str:
        """
        Generate a file with semantic memory retrieval.
        
        This is the preferred method that retrieves context from memory first.
        
        Args:
            file_path: Path of the file to generate
            
        Returns:
            File content as string
        """
        # Try to retrieve context from memory
        memory_context = self._retrieve_memory_context(file_path)
        return self.generate_file(file_path, memory_context)
    
    def _retrieve_memory_context(self, file_path: str) -> str:
        """
        Retrieve relevant context from semantic memory.
        
        Args:
            file_path: Path being generated
            
        Returns:
            Context string from memory
        """
        try:
            from backend.memory.retriever import retrieve_context
            
            # Build query from file path and roadmap
            query = f"{file_path} {self.roadmap.get('architecture', '')}"
            return retrieve_context(query, k=3)
        except ImportError:
            # Memory module not available
            return ""
        except Exception:
            return ""
    
    def _fallback_content(self, file_path: str) -> str:
        """Generate fallback content for a file."""
        if file_path.endswith(".json"):
            if "package" in file_path:
                return self._fallback_package_json()
            return "{}"
        elif file_path.endswith(".js") or file_path.endswith(".jsx"):
            return self._fallback_js(file_path)
        elif file_path.endswith(".css"):
            return self._fallback_css(file_path)
        elif file_path.endswith(".html"):
            return self._fallback_html()
        else:
            return f"// {file_path}\n// Generated by VibeCoder\n"
    
    def _fallback_package_json(self) -> str:
        return '''{
  "name": "vibe-app",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.1",
    "vite": "^5.4.2"
  }
}'''
    
    def _fallback_js(self, file_path: str) -> str:
        name = file_path.split("/")[-1].replace(".jsx", "").replace(".js", "")
        if "main" in file_path.lower():
            return '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)'''
        elif "App" in file_path:
            return '''import './App.css'

function App() {
  return (
    <div className="app">
      <h1>Welcome to VibeCoder</h1>
      <p>Your application is running!</p>
    </div>
  )
}

export default App'''
        else:
            return f'''// {name} Component
export default function {name}() {{
  return (
    <div className="{name.lower()}">
      {name}
    </div>
  )
}}'''
    
    def _fallback_css(self, file_path: str) -> str:
        return '''* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.6;
  color: #333;
}

.app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}'''
    
    def _fallback_html(self) -> str:
        return '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>VibeCoder App</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>'''
