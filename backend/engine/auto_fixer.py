"""
Auto-Fix Agent — LLM-powered test-fix loop (Plan Phase 2.3).

Identifies root cause from test failures, generates targeted fixes,
re-runs validation, and retries up to max_attempts times.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from backend.core.learning.failure_analyzer import FailureAnalyzer, ExecutionFailure, FailureAnalysis
from backend.engine.llm_gateway import llm_call_simple

logger = logging.getLogger("auto_fixer")


class FixAttempt(BaseModel):
    attempt: int
    fix_description: str
    fixed_code: Optional[str] = None
    success: bool
    error: Optional[str] = None


class FixResult(BaseModel):
    success: bool
    fix: Optional[str] = None          # human-readable fix description
    fixed_code: Optional[str] = None   # actual code patch if available
    attempts: int = 0
    attempts_log: List[FixAttempt] = []
    root_cause: str = ""
    confidence: float = 0.0


# ── Prompt templates ─────────────────────────────────────────────────────────

_ANALYZE_PROMPT = """You are an expert software debugger.

A test/execution failed. Analyze the failure and propose a concrete fix.

CODE (truncated):
{code}

ERROR:
{error}

STAGE: {stage}
ATTEMPT: {attempt}/{max_attempts}
PREVIOUS FIXES TRIED:
{previous_fixes}

Respond ONLY with valid JSON:
{{
  "root_cause": "Brief root cause analysis",
  "fix_description": "What exactly needs to change",
  "fixed_code": "The corrected code snippet (or null if not applicable)",
  "confidence": 0.85
}}"""


class AutoFixAgent:
    """
    Autonomously fix code/config issues using:
    1. FailureAnalyzer for pattern matching (fast, no LLM needed)
    2. LLM for deep analysis when pattern matching fails
    3. Test-fix loop with configurable max_attempts
    """

    def __init__(self) -> None:
        self.failure_analyzer = FailureAnalyzer()

    async def fix_issue(
        self,
        issue: Dict[str, Any],
        code: Any,
        max_attempts: int = 3,
        validator: Optional[Any] = None,  # optional async callable(code) -> bool
    ) -> FixResult:
        """
        Attempt to fix an issue with up to max_attempts LLM calls.

        Args:
            issue: dict with 'error'/'message'/'stage' keys
            code: the code/config that failed (str, dict, or any)
            max_attempts: max fix iterations
            validator: optional async callable to verify each fix attempt

        Returns:
            FixResult with success status, fix description, and attempt log
        """
        error_msg = issue.get("error", issue.get("message", "Unknown error"))
        stage = issue.get("stage", "execution")
        code_str = str(code)[:2000]

        # ── Fast path: pattern matching ───────────────────────────────────────
        failure = ExecutionFailure(
            stage=stage,
            agent="auto_fixer",
            error_message=error_msg,
            stack_trace=issue.get("stack_trace", ""),
            context={"code": code_str[:500]},
        )
        analysis: FailureAnalysis = await self.failure_analyzer.analyze_failure(failure)

        if analysis.confidence >= 0.9:
            logger.info("AutoFixer: high-confidence pattern match (%.0f%%)", analysis.confidence * 100)
            return FixResult(
                success=True,
                fix=analysis.recommended_fix,
                attempts=1,
                root_cause=analysis.root_cause,
                confidence=analysis.confidence,
                attempts_log=[FixAttempt(
                    attempt=1,
                    fix_description=analysis.recommended_fix,
                    success=True,
                )],
            )

        # ── LLM-powered test-fix loop ─────────────────────────────────────────
        previous_fixes: List[str] = []
        current_code = code_str

        for attempt in range(1, max_attempts + 1):
            logger.info("AutoFixer: LLM attempt %d/%d", attempt, max_attempts)

            prompt = _ANALYZE_PROMPT.format(
                code=current_code,
                error=error_msg,
                stage=stage,
                attempt=attempt,
                max_attempts=max_attempts,
                previous_fixes="\n".join(f"- {f}" for f in previous_fixes) or "None",
            )

            def _llm_call() -> Optional[str]:
                return llm_call_simple(
                    agent_name="auto_fixer",
                    system="You are an expert debugging agent. Always respond with valid JSON.",
                    user=prompt,
                    max_tokens=1500,
                    temperature=0.2,
                )

            try:
                raw = await asyncio.get_running_loop().run_in_executor(None, _llm_call)
                parsed = self._parse_response(raw)
            except Exception as exc:
                logger.warning("AutoFixer: LLM call failed: %s", exc)
                parsed = None

            if not parsed:
                attempts_log_entry = FixAttempt(
                    attempt=attempt,
                    fix_description="LLM response parsing failed",
                    success=False,
                    error="Failed to parse LLM response",
                )
                previous_fixes.append("Parse failure — retrying")
                continue

            fix_desc: str = parsed.get("fix_description", "")
            fixed_code: Optional[str] = parsed.get("fixed_code")
            root_cause: str = parsed.get("root_cause", analysis.root_cause)
            confidence: float = float(parsed.get("confidence", 0.5))

            previous_fixes.append(fix_desc)

            # Apply fix to working code if provided
            if fixed_code:
                current_code = fixed_code

            # Validate if a validator is provided
            if validator:
                try:
                    ok = await validator(current_code)
                except Exception as val_exc:
                    ok = False
                    error_msg = str(val_exc)
            else:
                # No validator — trust LLM confidence
                ok = confidence >= 0.75

            attempt_entry = FixAttempt(
                attempt=attempt,
                fix_description=fix_desc,
                fixed_code=fixed_code,
                success=ok,
                error=None if ok else f"Validation failed (confidence={confidence:.2f})",
            )

            if ok:
                logger.info("AutoFixer: fix succeeded on attempt %d", attempt)
                return FixResult(
                    success=True,
                    fix=fix_desc,
                    fixed_code=current_code if fixed_code else None,
                    attempts=attempt,
                    root_cause=root_cause,
                    confidence=confidence,
                    attempts_log=[attempt_entry],
                )

        # All attempts exhausted
        logger.warning("AutoFixer: all %d attempts failed", max_attempts)
        return FixResult(
            success=False,
            fix=previous_fixes[-1] if previous_fixes else analysis.recommended_fix,
            attempts=max_attempts,
            root_cause=analysis.root_cause,
            confidence=analysis.confidence,
        )

    def _parse_response(self, raw: Optional[str]) -> Optional[Dict[str, Any]]:
        """Parse LLM JSON response, stripping markdown fences."""
        if not raw:
            return None
        try:
            text = raw.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text.strip())
        except (json.JSONDecodeError, IndexError):
            return None
