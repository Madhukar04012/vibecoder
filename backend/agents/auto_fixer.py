"""
Auto-Fix Agent - Autonomous debugging and fixing (Phase 2.3)

Automatically fixes code issues based on test failures and error analysis.
Part of the self-improvement system.
"""

from __future__ import annotations

import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from backend.agents.base_society_agent import SocietyAgent
from backend.core.communication.message_bus import Message
from backend.core.documents.base import Document, DocumentType
from backend.core.documents.code_doc import CodeImplementationDocument, CodeImplementationContent
from backend.core.learning.failure_analyzer import FailureAnalyzer, ExecutionFailure, FailureAnalysis
from backend.engine.llm_gateway import llm_call_simple


class FixStatus(str, Enum):
    """Status of an auto-fix attempt."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    MAX_ATTEMPTS_REACHED = "max_attempts"


@dataclass
class FixAttempt:
    """Record of a fix attempt."""
    attempt_number: int
    issue_description: str
    fix_strategy: str
    changes_made: List[str]
    test_results: Optional[Dict[str, Any]]
    status: FixStatus
    error: Optional[str] = None


@dataclass
class FixResult:
    """Complete result of auto-fix process."""
    success: bool
    original_issue: str
    fix_attempts: List[FixAttempt]
    final_code: Optional[str]
    total_attempts: int
    status: FixStatus
    lessons_learned: List[str]


class AutoFixAgent(SocietyAgent):
    """
    Agent that automatically fixes code issues.
    
    Capabilities:
    1. Analyze test failures and error messages
    2. Generate targeted fixes
    3. Apply fixes and re-test
    4. Learn from successful fixes
    """

    role = "Auto-Fix Specialist"
    capabilities = [
        "analyze_failures",
        "generate_fixes", 
        "apply_patches",
        "verify_fixes",
        "learn_patterns"
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.failure_analyzer = FailureAnalyzer()
        self._fix_patterns: Dict[str, Dict[str, Any]] = {}
        self._successful_fixes: List[Dict[str, Any]] = []

    async def receive_message(self, msg: Message) -> Optional[Message]:
        """Handle incoming fix requests."""
        if msg.msg_type == "fix_request":
            issue = msg.payload.get("issue", {})
            code_doc_id = msg.payload.get("code_doc_id")
            
            result = await self.fix_issue(
                issue=issue,
                code_doc_id=code_doc_id,
                max_attempts=msg.payload.get("max_attempts", 3)
            )
            
            return Message(
                from_agent=self.name,
                to_agent=msg.from_agent,
                msg_type="fix_result",
                payload={
                    "success": result.success,
                    "status": result.status.value,
                    "attempts": result.total_attempts,
                    "lessons": result.lessons_learned,
                },
                in_response_to=msg.msg_id,
            )
        
        return None

    async def execute_task(self, task: Dict[str, Any]) -> Document:
        """Execute auto-fix task."""
        run_id = task.get("run_id", "default")
        issue = task.get("issue", {})
        code_doc_id = task.get("code_doc_id")
        
        result = await self.fix_issue(
            issue=issue,
            code_doc_id=code_doc_id,
            max_attempts=task.get("max_attempts", 3)
        )

        # Create result document
        from backend.core.documents.base import Document
        return Document(
            run_id=run_id,
            created_by=self.name,
            title=f"Auto-Fix Result: {result.status.value}",
            content={
                "success": result.success,
                "original_issue": result.original_issue,
                "total_attempts": result.total_attempts,
                "status": result.status.value,
                "lessons_learned": result.lessons_learned,
                "attempts": [
                    {
                        "attempt": a.attempt_number,
                        "strategy": a.fix_strategy,
                        "status": a.status.value,
                        "changes": a.changes_made,
                    }
                    for a in result.fix_attempts
                ],
            },
        )

    async def fix_issue(
        self,
        issue: Dict[str, Any],
        code_doc_id: Optional[str] = None,
        max_attempts: int = 3,
    ) -> FixResult:
        """
        Attempt to fix an issue automatically.
        
        Args:
            issue: Dictionary with error_message, stack_trace, context
            code_doc_id: ID of code document to fix
            max_attempts: Maximum number of fix attempts
            
        Returns:
            FixResult with details of the fix process
        """
        original_issue = issue.get("description", issue.get("error_message", "Unknown issue"))
        fix_attempts: List[FixAttempt] = []
        current_code = None

        # Get code to fix
        if code_doc_id:
            code_doc = self.document_store.get(code_doc_id)
            if code_doc and hasattr(code_doc, 'content'):
                current_code = str(code_doc.content)

        for attempt in range(1, max_attempts + 1):
            # Analyze the failure
            failure = ExecutionFailure(
                stage=issue.get("stage", "unknown"),
                agent=issue.get("agent", "unknown"),
                error_message=issue.get("error_message", ""),
                stack_trace=issue.get("stack_trace", ""),
                context=issue.get("context", {}),
            )
            
            analysis = await self.failure_analyzer.analyze_failure(failure)
            
            # Generate fix
            fix_strategy = self._determine_fix_strategy(analysis, attempt)
            
            if not current_code:
                # Can't fix without code
                fix_attempts.append(FixAttempt(
                    attempt_number=attempt,
                    issue_description=original_issue,
                    fix_strategy=fix_strategy,
                    changes_made=[],
                    test_results=None,
                    status=FixStatus.FAILED,
                    error="No code available to fix",
                ))
                break

            # Apply fix
            try:
                fixed_code, changes = await self._apply_fix(
                    code=current_code,
                    analysis=analysis,
                    strategy=fix_strategy,
                )
                
                # Verify fix (in real implementation, would run tests)
                test_results = await self._verify_fix(fixed_code, issue)
                
                if test_results.get("passed", False):
                    # Success!
                    fix_attempts.append(FixAttempt(
                        attempt_number=attempt,
                        issue_description=original_issue,
                        fix_strategy=fix_strategy,
                        changes_made=changes,
                        test_results=test_results,
                        status=FixStatus.SUCCESS,
                    ))
                    
                    # Store successful pattern
                    self._store_successful_fix(analysis, fix_strategy, changes)
                    
                    return FixResult(
                        success=True,
                        original_issue=original_issue,
                        fix_attempts=fix_attempts,
                        final_code=fixed_code,
                        total_attempts=attempt,
                        status=FixStatus.SUCCESS,
                        lessons_learned=self._extract_lessons(analysis, fix_attempts),
                    )
                else:
                    # Partial success - fix applied but tests still failing
                    fix_attempts.append(FixAttempt(
                        attempt_number=attempt,
                        issue_description=original_issue,
                        fix_strategy=fix_strategy,
                        changes_made=changes,
                        test_results=test_results,
                        status=FixStatus.PARTIAL,
                    ))
                    current_code = fixed_code  # Try fixing the new state
                    
            except Exception as e:
                fix_attempts.append(FixAttempt(
                    attempt_number=attempt,
                    issue_description=original_issue,
                    fix_strategy=fix_strategy,
                    changes_made=[],
                    test_results=None,
                    status=FixStatus.FAILED,
                    error=str(e),
                ))

        # Max attempts reached without success
        return FixResult(
            success=False,
            original_issue=original_issue,
            fix_attempts=fix_attempts,
            final_code=current_code,
            total_attempts=len(fix_attempts),
            status=FixStatus.MAX_ATTEMPTS_REACHED,
            lessons_learned=self._extract_lessons(None, fix_attempts),
        )

    def _determine_fix_strategy(self, analysis: FailureAnalysis, attempt: int) -> str:
        """Determine the best fix strategy based on failure analysis."""
        strategies = {
            "syntax_error": [
                "Fix syntax errors and indentation",
                "Add missing parentheses/brackets",
                "Correct import statements",
            ],
            "logic_error": [
                "Fix conditional logic",
                "Correct variable assignments",
                "Add missing error handling",
            ],
            "import_error": [
                "Add missing imports",
                "Fix import paths",
                "Install missing dependencies",
            ],
            "type_error": [
                "Add type conversions",
                "Fix function signatures",
                "Validate input types",
            ],
            "timeout": [
                "Optimize slow operations",
                "Add caching",
                "Break into smaller tasks",
            ],
            "api_error": [
                "Add retry logic",
                "Fix API endpoints",
                "Update authentication",
            ],
        }
        
        category = analysis.category.value if analysis else "unknown"
        category_strategies = strategies.get(category, ["General fix attempt"])
        
        # Cycle through strategies on multiple attempts
        return category_strategies[(attempt - 1) % len(category_strategies)]

    async def _apply_fix(
        self,
        code: str,
        analysis: FailureAnalysis,
        strategy: str,
    ) -> Tuple[str, List[str]]:
        """Apply fix to code based on strategy."""
        
        prompt = f"""Fix this code based on the error analysis.

STRATEGY: {strategy}
ERROR: {analysis.root_cause if analysis else 'Unknown error'}
RECOMMENDED FIX: {analysis.recommended_fix if analysis else 'General fix'}

CODE TO FIX:
```python
{code[:3000]}
```

Provide your fix as JSON:
{{
  "fixed_code": "the complete fixed code",
  "changes_made": ["description of change 1", "description of change 2"],
  "explanation": "brief explanation of what was fixed"
}}

Return ONLY valid JSON."""

        def _call_llm():
            return llm_call_simple(
                agent_name="auto_fix_agent",
                system="You are an expert code debugger. Fix the code and return valid JSON only.",
                user=prompt,
                max_tokens=3000,
                temperature=0.2,
            )

        response = await asyncio.get_running_loop().run_in_executor(None, _call_llm)
        
        if not response:
            return code, ["No fix generated"]

        try:
            # Extract JSON
            text = response.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            data = json.loads(text.strip())
            fixed_code = data.get("fixed_code", code)
            changes = data.get("changes_made", [])
            
            return fixed_code, changes
            
        except (json.JSONDecodeError, IndexError):
            return code, ["Failed to parse fix"]

    async def _verify_fix(self, code: str, original_issue: Dict[str, Any]) -> Dict[str, Any]:
        """Verify that the fix works (simplified version)."""
        # In a real implementation, this would:
        # 1. Run syntax check
        # 2. Run unit tests
        # 3. Check for the specific error
        
        # For now, do basic syntax check
        try:
            compile(code, '<string>', 'exec')
            return {"passed": True, "checks": ["syntax_ok"]}
        except SyntaxError as e:
            return {
                "passed": False,
                "checks": ["syntax_failed"],
                "error": str(e),
            }

    def _store_successful_fix(
        self,
        analysis: FailureAnalysis,
        strategy: str,
        changes: List[str],
    ) -> None:
        """Store a successful fix pattern for future reference."""
        pattern_key = f"{analysis.category.value}:{analysis.pattern}"
        
        if pattern_key not in self._fix_patterns:
            self._fix_patterns[pattern_key] = {
                "category": analysis.category.value,
                "pattern": analysis.pattern,
                "strategy": strategy,
                "changes": changes,
                "success_count": 0,
            }
        
        self._fix_patterns[pattern_key]["success_count"] += 1
        
        self._successful_fixes.append({
            "category": analysis.category.value,
            "pattern": analysis.pattern,
            "strategy": strategy,
            "changes": changes,
        })

    def _extract_lessons(
        self,
        analysis: Optional[FailureAnalysis],
        attempts: List[FixAttempt],
    ) -> List[str]:
        """Extract lessons learned from fix attempts."""
        lessons = []
        
        if analysis:
            lessons.append(f"Issue category: {analysis.category.value}")
            lessons.append(f"Root cause: {analysis.root_cause[:100]}")
        
        # Analyze what worked
        successful_strategies = [
            a.fix_strategy for a in attempts 
            if a.status == FixStatus.SUCCESS
        ]
        if successful_strategies:
            lessons.append(f"Successful strategy: {successful_strategies[0]}")
        
        # Track failures
        failed_attempts = [a for a in attempts if a.status == FixStatus.FAILED]
        if len(failed_attempts) == len(attempts):
            lessons.append("All fix attempts failed - manual intervention needed")
        
        return lessons[:5]  # Top 5 lessons

    def get_successful_patterns(self) -> List[Dict[str, Any]]:
        """Get patterns of successful fixes."""
        return sorted(
            self._successful_fixes,
            key=lambda x: self._fix_patterns.get(
                f"{x['category']}:{x['pattern']}", {}
            ).get("success_count", 0),
            reverse=True,
        )[:10]
