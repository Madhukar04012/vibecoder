"""
LLM Client - NVIDIA NIM / DeepSeek for AI inference (single pipeline).
All LLM calls go through NIM; no local Ollama.
"""

import os

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



def nim_chat(prompt: str) -> str | None:
    """
    Chat completion via NVIDIA NIM API (OpenAI-compatible).
    Uses NIM_API_KEY and NIM_MODEL from env.
    Supports DeepSeek V3.2 with advanced reasoning.
    """
    api_key = os.getenv("NIM_API_KEY", "").strip()
    if not api_key:
        return None
    model = os.getenv("NIM_MODEL", "deepseek-ai/deepseek-v3.2")
    enable_reasoning = os.getenv("NIM_REASONING", "true").lower() == "true"
    is_deepseek = "deepseek" in model.lower()
    use_reasoning = enable_reasoning and is_deepseek

    try:
        from openai import OpenAI

        client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key,
        )

        kwargs = dict(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=1 if use_reasoning else 0.3,
            top_p=0.95 if use_reasoning else 0.7,
            max_tokens=16384,
            stream=use_reasoning,
        )

        if use_reasoning:
            kwargs["extra_body"] = {"chat_template_kwargs": {"thinking": True}}

        if use_reasoning:
            stream = client.chat.completions.create(**kwargs)
            content_parts = []
            for chunk in stream:
                if not getattr(chunk, "choices", None):
                    continue
                delta = chunk.choices[0].delta
                if delta.content is not None:
                    content_parts.append(delta.content)
            content = "".join(content_parts).strip()
            return content or None
        else:
            completion = client.chat.completions.create(**kwargs)
            content = completion.choices[0].message.content if completion.choices else ""
            return content.strip() or None
    except ImportError:
        # Fallback to requests if openai SDK not available
        import requests
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        try:
            r = requests.post(
                url,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 16384,
                },
                timeout=120,
            )
            r.raise_for_status()
            data = r.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return content.strip() or None
        except Exception as e:
            print(f"[LLM] NIM chat error: {e}")
            return None
    except Exception as e:
        print(f"[LLM] NIM chat error: {e}")
        return None


def _parse_json_from_response(raw: str):
    """Try to extract and parse JSON from LLM response. Returns dict/list or None."""
    if not raw or not isinstance(raw, str):
        return None
    text = raw.strip()
    # Strip markdown code block if present
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end != -1:
            text = text[start:end].strip()
    elif "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end != -1:
            text = text[start:end].strip()
    # Find first { or [ for JSON
    for open_char, close_char in ("{[", "}]"):
        i = text.find(open_char)
        if i != -1:
            depth = 0
            for j in range(i, len(text)):
                if text[j] in "{[":
                    depth += 1
                elif text[j] in "}]":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[i : j + 1])
                        except json.JSONDecodeError:
                                break
            break
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def call_llm(prompt: str):
    """
    Single entry point for LLM completion (NIM/DeepSeek pipeline).
    Used by team_lead, task_manager, and studio. Returns parsed JSON when
    possible, else raw string. Returns: dict, list, or str; or None on failure.
    """
    raw = nim_chat(prompt)
    if raw is None:
        return None
    parsed = _parse_json_from_response(raw)
    if parsed is not None:
        return parsed
    return raw


def call_ollama(prompt: str):
    """Backward-compat name for call_llm. Use call_llm in new code."""
    return call_llm(prompt)

__all__ = ["nim_chat", "call_llm", "call_ollama"]
