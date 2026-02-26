"""
Model Speed Benchmark — VibeCober NIM Stack
Tests all 5 agent-role models for:
  - Time-to-first-token (TTFT)
  - Total latency (time to complete response)
  - Output token throughput (tokens/sec)
  - Token counts
Runs each model N times and reports min/avg/max.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Dict, List

# ── Path setup so we can import backend modules ────────────────────────────────
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))

from dotenv import load_dotenv
load_dotenv(root / ".env", override=True)

from openai import AsyncOpenAI

# ── Config ─────────────────────────────────────────────────────────────────────

NIM_BASE_URL   = "https://integrate.api.nvidia.com/v1"
NIM_API_KEY    = os.getenv("NIM_API_KEY") or os.getenv("NVIDIA_API_KEY", "")
RUNS_PER_MODEL = 3          # how many timed calls per model
MAX_TOKENS     = 128        # keep short to minimise cost & wait time
TIMEOUT        = 60.0       # seconds per call

# Minimal deterministic prompt — tests cold-start + token generation speed
SYSTEM_PROMPT = "You are a speed test assistant. Be concise."
USER_PROMPT   = (
    "List the five most important software engineering principles in one sentence each. "
    "Number them 1-5."
)

# ── Models under test ─────────────────────────────────────────────────────────

MODELS: List[Dict] = [
    {
        "role":  "team_lead",
        "model": "nvidia/llama-3.3-nemotron-super-49b-v1",
        "label": "Nemotron Super 49B",
        "temp":  0.5,
    },
    {
        "role":  "backend_engineer",
        "model": "mistralai/devstral-2-123b-instruct-2512",
        "label": "Devstral 2 123B",
        "temp":  0.15,
    },
    {
        "role":  "frontend_engineer",
        "model": "qwen/qwen2.5-coder-32b-instruct",
        "label": "Qwen 2.5 Coder 32B",
        "temp":  0.15,
    },
    {
        "role":  "database_engineer",
        "model": "meta/llama-3.3-70b-instruct",
        "label": "Llama 3.3 70B",
        "temp":  0.2,
    },
    {
        "role":  "qa_engineer",
        "model": "qwen/qwq-32b",
        "label": "QWQ 32B",
        "temp":  0.3,
    },
]


# ── Benchmark Core ─────────────────────────────────────────────────────────────

async def benchmark_model(client: AsyncOpenAI, cfg: Dict, run: int) -> Dict:
    """Stream one call; measure TTFT, total time, and token throughput."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": USER_PROMPT},
    ]

    t_start = time.monotonic()
    ttft: float | None = None
    output_chars = 0
    output_tokens = 0
    error: str | None = None

    try:
        stream = await client.chat.completions.create(
            model=cfg["model"],
            messages=messages,
            temperature=cfg["temp"],
            top_p=0.9,
            max_tokens=MAX_TOKENS,
            stream=True,
        )
        async for chunk in stream:
            if not chunk.choices:
                continue
            content = chunk.choices[0].delta.content or ""
            # Also grab reasoning_content if present (QWQ)
            reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None) or ""
            text = content + reasoning
            if text:
                if ttft is None:
                    ttft = time.monotonic() - t_start
                output_chars += len(text)
                output_tokens += 1   # each chunk ≈ 1 token in streaming

    except Exception as exc:
        error = str(exc)[:120]

    total_ms = (time.monotonic() - t_start) * 1000
    ttft_ms  = (ttft or 0) * 1000

    # Rough tokens/sec from chars (4 chars ≈ 1 token)
    approx_tok = max(output_chars // 4, 1)
    tok_per_sec = approx_tok / max((total_ms - ttft_ms) / 1000, 0.001)

    return {
        "run":       run,
        "ttft_ms":   round(ttft_ms,  1),
        "total_ms":  round(total_ms, 1),
        "chars":     output_chars,
        "approx_tok":approx_tok,
        "tok_per_sec": round(tok_per_sec, 1),
        "error":     error,
    }


async def run_all_benchmarks() -> Dict[str, List[Dict]]:
    """Run RUNS_PER_MODEL consecutive calls per model sequentially."""
    if not NIM_API_KEY or NIM_API_KEY.startswith("nvapi-your"):
        print("ERROR: NIM_API_KEY not configured. Set it in .env")
        return {}

    client = AsyncOpenAI(
        base_url=NIM_BASE_URL,
        api_key=NIM_API_KEY,
        timeout=TIMEOUT,
    )

    results: Dict[str, List[Dict]] = {}

    for cfg in MODELS:
        print(f"\n── Testing {cfg['label']} ({cfg['model']}) ──")
        runs = []
        for r in range(1, RUNS_PER_MODEL + 1):
            print(f"  Run {r}/{RUNS_PER_MODEL}...", end=" ", flush=True)
            result = await benchmark_model(client, cfg, r)
            runs.append(result)
            if result["error"]:
                print(f"ERROR: {result['error']}")
            else:
                print(
                    f"TTFT={result['ttft_ms']:.0f}ms  "
                    f"Total={result['total_ms']:.0f}ms  "
                    f"{result['tok_per_sec']:.0f} tok/s"
                )
            # Brief pause between runs to avoid rate limits
            await asyncio.sleep(0.5)
        results[cfg["role"]] = runs

    return results


# ── Report ─────────────────────────────────────────────────────────────────────

def compute_stats(runs: List[Dict]) -> Dict:
    ok = [r for r in runs if not r["error"]]
    if not ok:
        return {"ok": 0, "avg_ttft": None, "avg_total": None, "avg_tps": None,
                "min_total": None, "max_total": None}

    ttfts  = [r["ttft_ms"]    for r in ok]
    totals = [r["total_ms"]   for r in ok]
    tps    = [r["tok_per_sec"] for r in ok]

    return {
        "ok":        len(ok),
        "avg_ttft":  round(sum(ttfts)  / len(ttfts),  0),
        "avg_total": round(sum(totals) / len(totals), 0),
        "min_total": round(min(totals), 0),
        "max_total": round(max(totals), 0),
        "avg_tps":   round(sum(tps)    / len(tps),    1),
    }


def print_report(results: Dict[str, List[Dict]]) -> None:
    if not results:
        return

    print("\n")
    print("=" * 78)
    print("  MODEL SPEED BENCHMARK RESULTS")
    print(f"  Prompt: ~{len(USER_PROMPT)} chars | max_tokens={MAX_TOKENS} | runs={RUNS_PER_MODEL}")
    print("=" * 78)

    header = (
        f"{'Role':<20} {'Model':<28} "
        f"{'TTFT(ms)':>10} {'Avg(ms)':>9} {'Min(ms)':>8} {'Max(ms)':>8} {'tok/s':>7}"
    )
    print(header)
    print("-" * 78)

    rows = []
    for cfg in MODELS:
        role = cfg["role"]
        if role not in results:
            continue
        s = compute_stats(results[role])
        if s["ok"] == 0:
            rows.append((cfg, s, 999999))
        else:
            rows.append((cfg, s, s["avg_total"]))

    # Sort by average total latency (fastest first)
    rows.sort(key=lambda x: x[2])

    medals = ["#1", "#2", "#3", "#4", "#5"]
    for i, (cfg, s, _) in enumerate(rows):
        rank = medals[i] if i < len(medals) else "  "
        if s["ok"] == 0:
            print(
                f"{rank} {cfg['role']:<18} {cfg['label']:<28} "
                f"{'N/A':>10} {'ERROR':>9}"
            )
        else:
            print(
                f"{rank} {cfg['role']:<18} {cfg['label']:<28} "
                f"{s['avg_ttft']:>10.0f} "
                f"{s['avg_total']:>9.0f} "
                f"{s['min_total']:>8.0f} "
                f"{s['max_total']:>8.0f} "
                f"{s['avg_tps']:>7.1f}"
            )

    print("=" * 78)

    # ── Analysis ──────────────────────────────────────────────────────────────
    print("\nANALYSIS")
    print("--------")

    ok_rows = [(cfg, s) for cfg, s, _ in rows if s["ok"] > 0]
    if not ok_rows:
        print("No successful results to analyse.")
        return

    fastest = ok_rows[0]
    slowest = ok_rows[-1]
    best_ttft  = min(ok_rows, key=lambda x: x[1]["avg_ttft"])
    best_tps   = max(ok_rows, key=lambda x: x[1]["avg_tps"])

    print(f"  Fastest overall  : {fastest[0]['label']} — {fastest[1]['avg_total']:.0f}ms avg total")
    print(f"  Slowest overall  : {slowest[0]['label']} — {slowest[1]['avg_total']:.0f}ms avg total")
    print(f"  Best TTFT        : {best_ttft[0]['label']} — {best_ttft[1]['avg_ttft']:.0f}ms")
    print(f"  Highest throughput: {best_tps[0]['label']} — {best_tps[1]['avg_tps']:.1f} tok/s")

    if len(ok_rows) >= 2:
        speedup = slowest[1]["avg_total"] / fastest[1]["avg_total"]
        print(f"  Speed ratio      : {fastest[0]['label']} is {speedup:.1f}× faster than {slowest[0]['label']}")

    print()
    print("Metric definitions:")
    print("  TTFT(ms)  — Time to first token (network + model startup latency)")
    print("  Avg(ms)   — Average total wall-clock time across runs")
    print("  Min/Max   — Fastest / slowest run observed")
    print("  tok/s     — Approx output tokens per second (after first token)")
    print()

    print("Notes:")
    for cfg, s, _ in rows:
        errs = [r["error"] for r in results.get(cfg["role"], []) if r.get("error")]
        if errs:
            print(f"  {cfg['label']}: {len(errs)} failed run(s) — {errs[0]}")


# ── Entry Point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("VibeCober — NIM Model Speed Benchmark")
    print(f"API base : {NIM_BASE_URL}")
    print(f"Runs/model: {RUNS_PER_MODEL}  |  max_tokens: {MAX_TOKENS}")

    results = asyncio.run(run_all_benchmarks())
    print_report(results)
