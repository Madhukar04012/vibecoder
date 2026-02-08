#!/usr/bin/env python3
"""
Test NVIDIA NIM API key: connectivity, correctness, and response quality.
"""
import os
import json
import time
from pathlib import Path

# Load .env from project root
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

API_KEY = os.getenv("NIM_API_KEY", "").strip()
BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL = os.getenv("NIM_MODEL", "meta/llama-3.3-70b-instruct")


def _req(method, path, data=None):
    """Make HTTP request with Bearer auth."""
    import urllib.request
    import urllib.error
    url = f"{BASE_URL}{path}" if path.startswith("/") else f"{BASE_URL}/{path}"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def _err(msg):
    print(f"   [FAIL] {msg}")


def _ok(msg):
    print(f"   [OK] {msg}")


def test_api():
    """Test NIM API: auth, latency, and JSON output quality."""
    import urllib.request
    import urllib.error

    if not API_KEY:
        print("[FAIL] NIM_API_KEY not set in .env")
        return False

    print("=" * 60)
    print("NVIDIA NIM API Key Test")
    print("=" * 60)
    print(f"Model: {MODEL}")
    print(f"Key prefix: {API_KEY[:12]}...{API_KEY[-4:]}")
    print()

    # Test 0: List models (verify API key)
    print("[0] List Models (API Key + Auth)")
    try:
        models = _req("GET", "/models")
        all_ids = [m.get("id", "?") for m in models.get("data", [])]
        ids = all_ids[:15]
        _ok(f"Auth OK | {len(all_ids)} models total")
        code_models = [i for i in all_ids if "code" in i.lower() or "codellama" in i.lower() or "starcoder" in i.lower()]
        print(f"   Code-related models: {code_models[:10]}")
        if MODEL not in all_ids:
            print(f"   [WARN] Model '{MODEL}' not in catalog. Using first code model if available.")
            alt = code_models[0] if code_models else all_ids[0]
            print(f"   [INFO] Will try: {alt}")
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        _err(f"HTTP {e.code}: {body[:200]}")
        if e.code == 401:
            print("   -> Invalid or expired API key")
        elif e.code == 404:
            print("   -> Endpoint /models may not exist for this API")
        return False
    except Exception as e:
        _err(str(e))
        return False
    print()

    # Pick model: try llama-3.1-8b first (quickstart example), then code models
    all_ids = [m.get("id", "?") for m in models.get("data", [])]
    code_models = [i for i in all_ids if "code" in i.lower() or "codellama" in i.lower() or "starcoder" in i.lower()]
    # Quickstart uses meta/llama-3.1-8b-instruct - try that first for broader account access
    candidates = ["meta/llama-3.1-8b-instruct", "meta/llama-3.1-8b", "meta/codellama-70b"] + code_models + all_ids
    test_model = next((c for c in candidates if c in all_ids), all_ids[0])
    print(f"   Using model for completion: {test_model}")
    print()

    # Test 1: Simple completion (connectivity + auth)
    print("[1] Chat Completion (Connectivity + Latency)")
    prompt = 'Respond with ONLY this exact JSON, nothing else: [{"path":"test.ts","content":"export const x = 1"}]'
    payload = {
        "model": test_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 512,
        "temperature": 0.1,
    }

    try:
        start = time.time()
        body = _req("POST", "/chat/completions", payload)
        elapsed = time.time() - start

        if "choices" not in body or not body["choices"]:
            _err(f"Unexpected response: {json.dumps(body)[:200]}...")
            return False

        content = body["choices"][0].get("message", {}).get("content", "")
        usage = body.get("usage", {})

        _ok(f"Auth OK | Status 200 | Latency: {elapsed:.2f}s")
        print(f"   Tokens: in={usage.get('prompt_tokens', '?')} out={usage.get('completion_tokens', '?')}")
        print(f"   Response (first 400 chars): {repr(content[:400])}")
        print()

        # Test 2: JSON extraction (accuracy)
        print("[2] JSON Output Accuracy")
        content_clean = content.strip()
        if content_clean.startswith("```"):
            lines = content_clean.split("\n")
            content_clean = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        try:
            parsed = json.loads(content_clean)
            if isinstance(parsed, list):
                valid = [c for c in parsed if isinstance(c, dict) and "path" in c and "content" in c]
                _ok(f"Valid JSON array | {len(valid)} file change(s) with path+content")
                for v in valid[:2]:
                    print(f"      - {v.get('path')}: {len(v.get('content', ''))} chars")
            else:
                print(f"   [WARN] Parsed JSON but not array: {type(parsed)}")
        except json.JSONDecodeError as e:
            _err(f"Invalid JSON: {e}")
            print(f"   Raw: {content_clean[:200]}...")
        print()

        # Test 3: Usage / Proportion
        print("[3] Usage / Proportion")
        if usage:
            print(f"   prompt_tokens: {usage.get('prompt_tokens', 'N/A')}")
            print(f"   completion_tokens: {usage.get('completion_tokens', 'N/A')}")
            print(f"   total_tokens: {usage.get('total_tokens', 'N/A')}")
        else:
            print("   (No usage block in response)")
        print()

        print("=" * 60)
        print("[OK] API key is working")
        return True

    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode() if e.fp else ""
        except Exception:
            pass
        _err(f"HTTP {e.code}: {body[:300]}")
        if e.code == 401:
            print("   -> Invalid or expired API key")
        elif e.code == 404:
            print("   -> Model not found or wrong endpoint. Try meta/codellama-70b")
        elif e.code == 429:
            print("   -> Rate limit exceeded")
        return False
    except Exception as e:
        _err(str(e))
        return False


if __name__ == "__main__":
    test_api()
