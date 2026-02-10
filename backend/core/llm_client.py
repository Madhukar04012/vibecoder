"""
LLM Client - Interface to Ollama and NVIDIA NIM for AI inference
"""

import os
import subprocess

# Ensure .env is loaded
try:
    from dotenv import load_dotenv
    _root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    load_dotenv(os.path.join(_root, ".env"))
except Exception:
    pass
import json
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
    timeout = int(os.getenv("OLLAMA_TIMEOUT", "120"))
    try:
        ollama_path = _get_ollama_path()
        result = subprocess.run(
            [ollama_path, "run", model],
            input=prompt,
            capture_output=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )

        output = result.stdout.strip() if result.stdout else ""
        
        if not output:
            print("[LLM] Empty response from model")
            return None

        # Extract JSON: find outermost { } pair (handles nested JSON for planner/engineer)
        json_start = output.find("{")
        if json_start == -1:
            print("[LLM] No JSON found in response")
            return None

        depth = 0
        json_end = -1
        for i in range(json_start, len(output)):
            if output[i] == "{":
                depth += 1
            elif output[i] == "}":
                depth -= 1
                if depth == 0:
                    json_end = i + 1
                    break

        json_str = output[json_start:json_end] if json_end > json_start else output[json_start:]
        if not json_str.endswith("}"):
            json_str = output[json_start:output.rfind("}") + 1]  # fallback to last }

        # Fix common LLM JSON issues
        json_str = json_str.replace("'", '"')
        json_str = re.sub(r',\s*}', '}', json_str)  # trailing commas in objects
        json_str = re.sub(r',\s*]', ']', json_str)  # trailing commas in arrays
        
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


def ollama_chat(prompt: str, model: str | None = None) -> str | None:
    """
    Simple chat completion via Ollama HTTP API.
    Returns the model's text response, or None if unavailable.
    """
    import requests
    model = model or os.getenv("OLLAMA_CHAT_MODEL", "llama3.2")
    url = "http://localhost:11434/api/generate"
    try:
        r = requests.post(
            url,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=30,
        )
        r.raise_for_status()
        return r.json().get("response", "").strip() or None
    except Exception as e:
        print(f"[LLM] Chat error: {e}")
        return None


def nim_chat(prompt: str) -> str | None:
    """
    Chat completion via NVIDIA NIM API (OpenAI-compatible).
    Uses NIM_API_KEY and NIM_MODEL from env.
    """
    import requests
    api_key = os.getenv("NIM_API_KEY", "").strip()
    if not api_key:
        return None
    model = os.getenv("NIM_MODEL", "meta/llama-3.3-70b-instruct")
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    try:
        r = requests.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1024,
            },
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return content.strip() or None
    except requests.exceptions.RequestException as e:
        err = getattr(e, "response", None)
        body = err.text if err else str(e)
        print(f"[LLM] NIM chat error: {e} | {body[:200] if body else ''}")
        return None
    except Exception as e:
        print(f"[LLM] NIM chat error: {e}")
        return None
