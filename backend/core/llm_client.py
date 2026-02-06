"""
LLM Client - Interface to local Ollama for AI inference
This is the ONLY file that knows about Ollama.
"""

import subprocess
import json
import os
import re
import sys


def _get_ollama_path() -> str:
    """Get Ollama executable path - cross-platform."""
    env_path = os.getenv("OLLAMA_PATH")
    if env_path:
        return env_path
    if sys.platform == "win32":
        return os.path.expanduser("~\\AppData\\Local\\Programs\\Ollama\\ollama.exe")
    # Linux/macOS - ollama is typically in PATH
    return "ollama"


def call_ollama(prompt: str, model: str = "mistral"):
    """
    Call local Ollama model and return parsed JSON response.
    Returns None if anything fails (timeout, parse error, etc.)
    """
    try:
        ollama_path = _get_ollama_path()
        result = subprocess.run(
            [ollama_path, "run", model],
            input=prompt,
            capture_output=True,
            timeout=120,
            encoding='utf-8',
            errors='replace'
        )

        output = result.stdout.strip() if result.stdout else ""
        
        if not output:
            print("[LLM] Empty response from model")
            return None

        # Try to extract JSON from response - look for JSON block
        json_match = re.search(r'\{[^{}]*"project_type"[^{}]*\}', output, re.DOTALL)
        
        if json_match:
            json_str = json_match.group()
            # Clean up common issues
            json_str = json_str.replace("'", '"')  # Single to double quotes
            return json.loads(json_str)
        
        # Fallback: try to find any JSON object
        json_start = output.find("{")
        json_end = output.rfind("}") + 1
        
        if json_start == -1 or json_end == 0:
            print("[LLM] No JSON found in response")
            return None
            
        json_str = output[json_start:json_end]
        
        # Try to fix common JSON issues
        json_str = json_str.replace("'", '"')
        json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
        json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas in arrays
        
        return json.loads(json_str)

    except subprocess.TimeoutExpired:
        print("[LLM] Request timed out (model may still be loading)")
        return None
    except json.JSONDecodeError as e:
        print(f"[LLM] JSON parse error: {e}")
        return None
    except FileNotFoundError:
        print("[LLM] Ollama not found - make sure it's installed")
        return None
    except Exception as e:
        print(f"[LLM] Unexpected error: {e}")
        return None
