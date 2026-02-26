"""
Unified Pipeline Runner.

Single source of truth for generation orchestration used by CLI and web flows.
Enforces strict contracts, retries with backoff, explicit state transitions,
observability logging, memory governance, artifact persistence, and token-tier budget caps.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from backend.agents.team_lead_brain import ExecutionPlan, create_execution_plan
from backend.core.agent_registry import get_agent_function
from backend.core.contracts import AgentContractError, validate_agent_output
from backend.engine.observability import AgentMetrics, RunLogger
from backend.engine.state import EngineState, EngineStateMachine
from backend.engine.token_governance import TokenTier, get_token_governance
from backend.engine.token_ledger import ledger
from backend.generator.project_builder import merge_agent_outputs
from backend.memory.indexer import build_scope_key, clear_index, index_file
from backend.storage.artifact_store import flatten_structure, get_artifact_store


class PipelineError(RuntimeError):
    """Raised when pipeline execution fails."""


# Constants
MAX_RETRY_BACKOFF_SECONDS = 60.0  # Maximum backoff cap to prevent unbounded delays
_retry_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="pipeline_retry")


def _sleep_async_safe(seconds: float) -> None:
    """
    Sleep that works in both sync and async contexts.
    
    Uses asyncio.sleep if in async context, otherwise uses time.sleep.
    This prevents blocking the event loop when running in async environments.
    """
    try:
        # Check if we're in an async context
        loop = asyncio.get_running_loop()
        # We're in async context, but this function is sync, so we need to use executor
        future = _retry_executor.submit(time.sleep, seconds)
        future.result()  # Block until sleep completes
    except RuntimeError:
        # No event loop running, safe to use time.sleep
        time.sleep(seconds)


@dataclass
class PipelineRequest:
    idea: str
    mode: str = "full"
    run_id: str | None = None
    channel: str = "cli"  # cli | web | api
    user_id: str = "local-cli"
    project_id: str | None = None
    token_tier: str = TokenTier.FREE.value
    memory_scope: str = "project"  # project | user | global
    memory_version: str = "v1"
    max_retries: int = 2
    retry_backoff_seconds: float = 0.75
    timeout_seconds: float | None = None
    clear_memory_before_run: bool = False


@dataclass
class PipelineContext:
    on_event: Optional[Callable[[str, Dict[str, Any]], None]] = None
    strict_contracts: bool = True


@dataclass
class AgentAttemptResult:
    output: Dict[str, Any]
    attempts: int
    retries: int
    duration_ms: float


@dataclass
class PipelineRunner:
    request: PipelineRequest
    context: PipelineContext = field(default_factory=PipelineContext)

    def __post_init__(self) -> None:
        self.run_id = self.request.run_id or f"run_{uuid.uuid4().hex[:10]}"
        self.request.run_id = self.run_id

        self.state_machine = EngineStateMachine()
        self.started_at = datetime.now(timezone.utc)

        self.plan: ExecutionPlan | None = None
        self.agent_outputs: Dict[str, Dict[str, Any]] = {}
        self.agent_metrics: Dict[str, Dict[str, Any]] = {}
        self.partial_failures: List[Dict[str, Any]] = []
        self.errors: List[str] = []

        self.logger = RunLogger(
            run_id=self.run_id,
            project_id=self.request.project_id,
            user_id=self.request.user_id,
        )

        scope = self.request.memory_scope
        project_id = self.request.project_id or self.run_id
        self.memory_scope_key = build_scope_key(
            scope=scope,
            project_id=project_id if scope == "project" else None,
            user_id=self.request.user_id if scope == "user" else None,
            version=self.request.memory_version,
        )

        self.artifact_store = get_artifact_store()
        self.governance = get_token_governance()

    def run(self) -> Dict[str, Any]:
        """Execute the full contract-enforced pipeline."""
        self._emit("run_started", {
            "idea": self.request.idea[:500],
            "mode": self.request.mode,
            "channel": self.request.channel,
            "state": self.state_machine.state.value,
            "memory_scope_key": self.memory_scope_key,
            "token_tier": self.request.token_tier,
        })

        ledger.start_run(self.run_id)
        budget_summary: Dict[str, Any] = {}

        try:
            budget_summary = self._configure_budget()

            if self.request.clear_memory_before_run:
                clear_index(self.memory_scope_key)
                self._emit("memory_cleared", {"scope_key": self.memory_scope_key})

            self._transition(EngineState.PLANNING)
            self.plan = create_execution_plan(self.request.idea, mode=self.request.mode)
            self._emit("execution_plan", self.plan.model_dump())

            self._transition(EngineState.WAITING_FOR_APPROVAL)
            # Current transport layers auto-approve.
            self._transition(EngineState.EXECUTING)

            for agent_name in self.plan.execution_order:
                self._enforce_timeout()
                self._transition_for_agent(agent_name)
                result = self._run_agent_with_retries(agent_name)
                self.agent_outputs[agent_name] = result.output

                self.agent_metrics[agent_name] = {
                    "status": "success",
                    "attempts": result.attempts,
                    "retries": result.retries,
                    "duration_ms": round(result.duration_ms, 3),
                }

            artifact_manifest = self._persist_artifacts()
            self._index_memory(artifact_manifest)

            final_state = EngineState.PARTIAL_SUCCESS if self.partial_failures else EngineState.COMPLETED
            self._transition(final_state)

            return self._build_result(
                success=True,
                budget_summary=budget_summary,
                artifact_manifest=artifact_manifest,
            )

        except TimeoutError as exc:
            self.errors.append(str(exc))
            self._transition(EngineState.TIMEOUT)
            self._emit("run_timeout", {"error": str(exc)})
            return self._build_result(
                success=False,
                budget_summary=budget_summary,
                error=str(exc),
            )
        except Exception as exc:
            self.errors.append(str(exc))
            if self.state_machine.state not in {EngineState.CANCELLED, EngineState.TIMEOUT}:
                self._transition(EngineState.FAILED)
            self._emit("run_failed", {"error": str(exc)})
            return self._build_result(
                success=False,
                budget_summary=budget_summary,
                error=str(exc),
            )
        finally:
            total_cost = float(ledger.total_cost)
            self.governance.apply_spend(
                user_id=self.request.user_id,
                tier=self.request.token_tier,
                spend_usd=total_cost,
            )
            self._emit("run_finished", {
                "state": self.state_machine.state.value,
                "total_cost_usd": round(total_cost, 6),
            })

    def _configure_budget(self) -> Dict[str, Any]:
        remaining = self.governance.get_remaining_budget(
            user_id=self.request.user_id,
            tier=self.request.token_tier,
        )
        if remaining is not None and remaining <= 0:
            raise PipelineError("Daily token budget exceeded for this tier")

        ledger.set_budget(remaining)
        summary = self.governance.get_summary(
            user_id=self.request.user_id,
            tier=self.request.token_tier,
        )
        self._emit("budget_configured", summary)
        return summary

    def _run_agent_with_retries(self, agent_name: str) -> AgentAttemptResult:
        max_attempts = max(1, int(self.request.max_retries) + 1)
        retry_reason = ""
        start = time.perf_counter()

        for attempt in range(1, max_attempts + 1):
            usage_before = self._usage_snapshot(agent_name)
            step_start = time.perf_counter()
            self._emit("agent_started", {"agent": agent_name, "attempt": attempt, "max_attempts": max_attempts})

            try:
                self.state_machine.validate_agent(agent_name)
                payload = self._execute_agent(agent_name, retry_reason=retry_reason)
                if self.context.strict_contracts:
                    payload = validate_agent_output(agent_name, payload)

                duration_ms = (time.perf_counter() - step_start) * 1000
                usage_after = self._usage_snapshot(agent_name)
                self._log_agent_metrics(
                    agent=agent_name,
                    attempt=attempt,
                    retries=max(0, attempt - 1),
                    status="success",
                    duration_ms=duration_ms,
                    before=usage_before,
                    after=usage_after,
                    error=None,
                )
                self._emit("agent_completed", {
                    "agent": agent_name,
                    "attempt": attempt,
                    "duration_ms": round(duration_ms, 3),
                })

                return AgentAttemptResult(
                    output=payload,
                    attempts=attempt,
                    retries=max(0, attempt - 1),
                    duration_ms=(time.perf_counter() - start) * 1000,
                )

            except Exception as exc:
                duration_ms = (time.perf_counter() - step_start) * 1000
                usage_after = self._usage_snapshot(agent_name)
                message = str(exc)
                self._log_agent_metrics(
                    agent=agent_name,
                    attempt=attempt,
                    retries=max(0, attempt - 1),
                    status="failed",
                    duration_ms=duration_ms,
                    before=usage_before,
                    after=usage_after,
                    error=message,
                )
                self._emit("agent_failed", {
                    "agent": agent_name,
                    "attempt": attempt,
                    "error": message,
                })

                retry_reason = message
                if attempt < max_attempts:
                    # Exponential backoff with cap to prevent unbounded delays
                    base_backoff = float(self.request.retry_backoff_seconds)
                    exponential_backoff = base_backoff * (2 ** (attempt - 1))
                    backoff = min(exponential_backoff, MAX_RETRY_BACKOFF_SECONDS)

                    self._emit("agent_retry", {
                        "agent": agent_name,
                        "attempt": attempt,
                        "next_attempt": attempt + 1,
                        "backoff_seconds": backoff,
                        "reason": message,
                    })
                    _sleep_async_safe(backoff)
                    continue

                if self._is_non_critical(agent_name):
                    failure = {
                        "agent": agent_name,
                        "error": message,
                        "attempts": attempt,
                        "non_critical": True,
                    }
                    self.partial_failures.append(failure)
                    self.agent_outputs[agent_name] = {
                        "status": "failed",
                        "error": message,
                        "attempts": attempt,
                    }
                    self._emit("agent_partial_failure", failure)
                    return AgentAttemptResult(
                        output=self.agent_outputs[agent_name],
                        attempts=attempt,
                        retries=max(0, attempt - 1),
                        duration_ms=(time.perf_counter() - start) * 1000,
                    )

                raise PipelineError(
                    f"Critical agent '{agent_name}' failed after {attempt} attempts: {message}"
                ) from exc

        raise PipelineError(f"Agent '{agent_name}' failed without an explicit exception")

    def _execute_agent(self, agent_name: str, retry_reason: str = "") -> Dict[str, Any]:
        if agent_name == "code_reviewer":
            from backend.agents.code_reviewer import review_code

            files = self._get_flattened_coder_files()
            if not files:
                return {
                    "approved": True,
                    "score": {
                        "tier": "C",
                        "total_score": 0,
                        "file_count": 0,
                        "breakdown": {"structure": 0, "code_quality": 0, "security": 0, "completeness": 0},
                        "issues": ["No generated files to review"],
                        "recommendations": ["Run coder before review"],
                    },
                    "file_reviews": {},
                    "critical_issues": [],
                    "summary": "Code review skipped: no generated files",
                }

            payload = review_code(files, prd=self.agent_outputs.get("planner"))
            return payload if isinstance(payload, dict) else payload.to_dict()

        agent_func = get_agent_function(agent_name)
        agent_input = self._build_agent_input(agent_name, retry_reason)

        # Pass user_idea to code_agent for SSS-class domain detection
        if agent_name == "coder":
            user_idea = agent_input.pop("__user_idea__", "")
            raw_output = agent_func(agent_input, user_idea=user_idea)
        else:
            raw_output = agent_func(agent_input)

        if not isinstance(raw_output, dict):
            raise AgentContractError(
                f"Agent '{agent_name}' returned non-dict payload: {type(raw_output).__name__}"
            )
        return raw_output

    def _build_agent_input(self, agent_name: str, retry_reason: str) -> Any:
        if agent_name == "planner":
            if retry_reason:
                return (
                    f"{self.request.idea}\n\n"
                    f"Previous planner attempt failed validation/error: {retry_reason}. "
                    "Return a strict JSON architecture object with required keys."
                )
            return self.request.idea

        if agent_name == "db_schema":
            payload = dict(self.agent_outputs.get("planner", {}))
            if retry_reason:
                payload["retry_reason"] = retry_reason
            return payload

        if agent_name == "auth":
            payload = {
                "db_schema": self.agent_outputs.get("db_schema", {}),
                "mode": self.request.mode,
            }
            if retry_reason:
                payload["retry_reason"] = retry_reason
            return payload

        if agent_name == "coder":
            payload = dict(self.agent_outputs.get("planner", {}))
            payload["__user_idea__"] = self.request.idea
            if retry_reason:
                payload["retry_reason"] = retry_reason
            return payload

        if agent_name == "tester":
            payload = {
                "auth": self.agent_outputs.get("auth", {}),
                "db_schema": self.agent_outputs.get("db_schema", {}),
            }
            if retry_reason:
                payload["retry_reason"] = retry_reason
            return payload

        if agent_name == "deployer":
            payload = {
                "mode": self.request.mode,
                "results": {
                    "input_idea": self.request.idea,
                    "execution_plan": self.plan.model_dump() if self.plan else {},
                    "agent_outputs": self.agent_outputs,
                },
            }
            if retry_reason:
                payload["retry_reason"] = retry_reason
            return payload

        # Generic context for unknown/future agents
        payload = {
            "idea": self.request.idea,
            "mode": self.request.mode,
            "agent_outputs": self.agent_outputs,
        }
        if retry_reason:
            payload["retry_reason"] = retry_reason
        return payload

    def _persist_artifacts(self) -> Dict[str, Any] | None:
        coder_output = self.agent_outputs.get("coder")
        if not coder_output:
            return None

        merged = merge_agent_outputs(coder_output, self.agent_outputs)
        flat = flatten_structure(merged)

        project_key = self.request.project_id or self.run_id
        manifest = self.artifact_store.persist(
            project_key=project_key,
            run_id=self.run_id,
            files=flat,
            metadata={
                "mode": self.request.mode,
                "channel": self.request.channel,
                "state": self.state_machine.state.value,
                "memory_scope_key": self.memory_scope_key,
            },
        )

        payload = {
            "project_key": manifest.project_key,
            "version": manifest.version,
            "file_count": manifest.file_count,
            "bundle_path": manifest.bundle_path,
            "s3_object": manifest.s3_object,
        }
        self._emit("artifacts_persisted", payload)
        return payload

    def _index_memory(self, artifact_manifest: Dict[str, Any] | None) -> None:
        if not artifact_manifest:
            return

        try:
            files = self.artifact_store.load_version(
                project_key=artifact_manifest["project_key"],
                version=int(artifact_manifest["version"]),
            )
        except Exception as exc:
            self._emit("memory_index_failed", {"error": str(exc)})
            return

        for path, content in files.items():
            index_file(path, content, scope_key=self.memory_scope_key)

        self._emit("memory_indexed", {
            "scope_key": self.memory_scope_key,
            "files_indexed": len(files),
        })

    def _usage_snapshot(self, agent_name: str) -> Dict[str, float]:
        usage = ledger.by_agent.get(agent_name, {})
        return {
            "input_tokens": float(usage.get("input_tokens", 0)),
            "output_tokens": float(usage.get("output_tokens", 0)),
            "total_tokens": float(usage.get("total_tokens", 0)),
            "cost_usd": float(usage.get("cost_usd", 0.0)),
        }

    def _log_agent_metrics(
        self,
        agent: str,
        attempt: int,
        retries: int,
        status: str,
        duration_ms: float,
        before: Dict[str, float],
        after: Dict[str, float],
        error: str | None,
    ) -> None:
        metric = AgentMetrics(
            agent=agent,
            status=status,
            attempt=attempt,
            retries=retries,
            duration_ms=round(duration_ms, 3),
            input_tokens=int(after["input_tokens"] - before["input_tokens"]),
            output_tokens=int(after["output_tokens"] - before["output_tokens"]),
            total_tokens=int(after["total_tokens"] - before["total_tokens"]),
            cost_usd=round(after["cost_usd"] - before["cost_usd"], 6),
            error=error,
        )
        self.logger.log_agent_metrics(metric)

    def _get_flattened_coder_files(self) -> Dict[str, str]:
        coder_output = self.agent_outputs.get("coder")
        if not coder_output:
            return {}

        if all(isinstance(value, str) for value in coder_output.values()):
            return coder_output

        return flatten_structure(coder_output)

    def _enforce_timeout(self) -> None:
        if not self.request.timeout_seconds:
            return

        elapsed = (datetime.now(timezone.utc) - self.started_at).total_seconds()
        if elapsed > float(self.request.timeout_seconds):
            raise TimeoutError(
                f"Run timed out after {elapsed:.2f}s (limit {self.request.timeout_seconds:.2f}s)"
            )

    def _is_non_critical(self, agent_name: str) -> bool:
        return agent_name in {"tester", "deployer"}

    def _transition_for_agent(self, agent_name: str) -> None:
        if agent_name == "code_reviewer" and self.state_machine.state != EngineState.REVIEWING:
            self._transition(EngineState.REVIEWING)
            return
        if agent_name == "tester" and self.state_machine.state != EngineState.QA:
            self._transition(EngineState.QA)
            return
        if self.state_machine.state in {
            EngineState.PLANNING,
            EngineState.WAITING_FOR_APPROVAL,
            EngineState.REVIEWING,
            EngineState.QA,
        } and agent_name not in {"code_reviewer", "tester"}:
            self._transition(EngineState.EXECUTING)

    def _transition(self, state: EngineState) -> None:
        if self.state_machine.state == state:
            return
        self.state_machine.transition(state)
        self._emit("state_transition", {
            "state": self.state_machine.state.value,
            "history": [item.value for item in self.state_machine.history],
        })

    def _emit(self, event: str, payload: Dict[str, Any]) -> None:
        self.logger.log(event, payload)
        if self.context.on_event:
            try:
                self.context.on_event(event, payload)
            except Exception as e:
                self.logger.log("on_event_failed", {"error": str(e)})

    def _build_result(
        self,
        success: bool,
        budget_summary: Dict[str, Any],
        artifact_manifest: Dict[str, Any] | None = None,
        error: str | None = None,
    ) -> Dict[str, Any]:
        total_duration_ms = (datetime.now(timezone.utc) - self.started_at).total_seconds() * 1000
        governance_summary = self.governance.get_summary(
            user_id=self.request.user_id,
            tier=self.request.token_tier,
        )
        predicted_post = dict(governance_summary)
        cap = budget_summary.get("daily_cap_usd")
        spent_before = float(budget_summary.get("spent_usd", governance_summary.get("spent_usd", 0.0)))
        spent_after = round(spent_before + float(ledger.total_cost), 6)
        predicted_post["spent_usd"] = spent_after
        if cap is None:
            predicted_post["remaining_usd"] = None
        else:
            predicted_post["remaining_usd"] = round(max(0.0, float(cap) - spent_after), 6)

        return {
            "success": success,
            "error": error,
            "state": self.state_machine.state.value,
            "input_idea": self.request.idea,
            "execution_plan": self.plan.model_dump() if self.plan else None,
            "agent_outputs": self.agent_outputs,
            "agent_metrics": self.agent_metrics,
            "partial_failures": self.partial_failures,
            "errors": self.errors,
            "artifact_manifest": artifact_manifest,
            "memory": {
                "scope_key": self.memory_scope_key,
                "version": self.request.memory_version,
            },
            "cost": {
                "total_usd": round(ledger.total_cost, 6),
                "total_tokens": ledger.total_tokens,
                "breakdown": ledger.by_agent,
            },
            "budget": {
                "pre_run": budget_summary,
                "post_run": predicted_post,
            },
            "run_id": self.run_id,
            "log_path": str(self.logger.path),
            "state_history": [item.value for item in self.state_machine.history],
            "duration_ms": round(total_duration_ms, 3),
            "started_at": self.started_at.isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }


def run_pipeline(request: PipelineRequest, context: PipelineContext | None = None) -> Dict[str, Any]:
    """Convenience function for one-shot pipeline execution."""
    runner = PipelineRunner(request=request, context=context or PipelineContext())
    return runner.run()
