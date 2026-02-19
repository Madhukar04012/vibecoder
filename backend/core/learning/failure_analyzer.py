"""Failure analyzer - root cause and recommended fix (plan Phase 2.2)."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum
from collections import defaultdict

class FailureSeverity(str, Enum):
    """Severity levels for failures."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class FailureCategory(str, Enum):
    """Categories of failures."""
    SYNTAX_ERROR = "syntax_error"
    LOGIC_ERROR = "logic_error"
    IMPORT_ERROR = "import_error"
    TYPE_ERROR = "type_error"
    RUNTIME_ERROR = "runtime_error"
    TIMEOUT = "timeout"
    API_ERROR = "api_error"
    VALIDATION_ERROR = "validation_error"
    CONFIG_ERROR = "config_error"
    DEPENDENCY_ERROR = "dependency_error"
    UNKNOWN = "unknown"

class ExecutionFailure(BaseModel):
    stage: str
    agent: str
    error_message: str
    stack_trace: str = ""
    context: Dict[str, Any] = {}

class FailurePattern(BaseModel):
    """A recognized pattern of failures."""
    pattern_id: str
    name: str
    category: FailureCategory
    symptoms: List[str]
    solution: str
    confidence: float = 0.8
    occurrence_count: int = 0

class FailureAnalysis(BaseModel):
    known_issue: bool = False
    root_cause: str = ""
    recommended_fix: str = ""
    pattern: Optional[str] = None
    confidence: float = 0.0
    category: FailureCategory = FailureCategory.UNKNOWN
    severity: FailureSeverity = FailureSeverity.MEDIUM

class FailureAnalyzer:
    """Advanced failure analyzer with pattern matching and statistics."""
    
    def __init__(self) -> None:
        self._patterns: List[FailurePattern] = self._load_default_patterns()
        self._failure_history: List[Dict[str, Any]] = []
        self._agent_failure_counts: Dict[str, int] = defaultdict(int)
        self._category_counts: Dict[FailureCategory, int] = defaultdict(int)

    def _load_default_patterns(self) -> List[FailurePattern]:
        """Load default failure patterns for common issues."""
        return [
            FailurePattern(
                pattern_id="timeout",
                name="Execution Timeout",
                category=FailureCategory.TIMEOUT,
                symptoms=["timeout", "timed out", "deadline exceeded"],
                solution="Increase timeout or optimize operation",
                confidence=0.95,
            ),
            FailurePattern(
                pattern_id="json_parse",
                name="JSON Parse Error",
                category=FailureCategory.SYNTAX_ERROR,
                symptoms=["json", "parse", "invalid json", "jsondecodeerror"],
                solution="Validate JSON format and ask LLM for valid JSON only",
                confidence=0.9,
            ),
            FailurePattern(
                pattern_id="auth_error",
                name="Authentication Error",
                category=FailureCategory.API_ERROR,
                symptoms=["auth", "401", "unauthorized", "authentication"],
                solution="Check credentials and refresh token",
                confidence=0.85,
            ),
            FailurePattern(
                pattern_id="import_error",
                name="Import/Module Error",
                category=FailureCategory.IMPORT_ERROR,
                symptoms=["module not found", "importerror", "no module named"],
                solution="Install missing dependencies or check import paths",
                confidence=0.9,
            ),
            FailurePattern(
                pattern_id="key_error",
                name="Missing Dictionary Key",
                category=FailureCategory.LOGIC_ERROR,
                symptoms=["keyerror", "key not found"],
                solution="Check dictionary keys before accessing or use .get() with default",
                confidence=0.88,
            ),
            FailurePattern(
                pattern_id="type_error",
                name="Type Mismatch",
                category=FailureCategory.TYPE_ERROR,
                symptoms=["typeerror", "unsupported operand", "cannot concatenate"],
                solution="Check variable types and ensure compatibility",
                confidence=0.85,
            ),
            FailurePattern(
                pattern_id="indentation_error",
                name="Indentation Error",
                category=FailureCategory.SYNTAX_ERROR,
                symptoms=["indentationerror", "unexpected indent", "taberror"],
                solution="Fix indentation: use consistent spaces or tabs, check alignment of code blocks",
                confidence=0.93,
            ),
            FailurePattern(
                pattern_id="python_syntax",
                name="Python Syntax Error",
                category=FailureCategory.SYNTAX_ERROR,
                symptoms=["syntaxerror", "invalid syntax", "unexpected eof"],
                solution="Fix Python syntax: check missing colons, parentheses, and brackets",
                confidence=0.92,
            ),
            FailurePattern(
                pattern_id="runtime_error",
                name="Runtime Error",
                category=FailureCategory.RUNTIME_ERROR,
                symptoms=["runtimeerror", "zerodivisionerror", "recursionerror", "overflowerror"],
                solution="Add error handling and validate inputs before operations",
                confidence=0.88,
            ),
            FailurePattern(
                pattern_id="attribute_error",
                name="Attribute Error",
                category=FailureCategory.LOGIC_ERROR,
                symptoms=["attributeerror", "has no attribute", "object has no"],
                solution="Check object type before accessing attributes, use hasattr() guard",
                confidence=0.87,
            ),
        ]

    async def analyze_failure(self, failure: ExecutionFailure) -> FailureAnalysis:
        """Analyze a failure using pattern matching and return detailed analysis."""
        msg = failure.error_message.lower()
        
        # Track the failure
        self._agent_failure_counts[failure.agent] += 1
        
        # Try pattern matching
        for pattern in self._patterns:
            if any(symptom.lower() in msg for symptom in pattern.symptoms):
                pattern.occurrence_count += 1
                self._category_counts[pattern.category] += 1
                
                self._failure_history.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "agent": failure.agent,
                    "category": pattern.category.value,
                    "pattern": pattern.name,
                    "message": failure.error_message[:200],
                })
                
                return FailureAnalysis(
                    known_issue=True,
                    root_cause=pattern.name,
                    recommended_fix=pattern.solution,
                    pattern=pattern.pattern_id,
                    confidence=pattern.confidence,
                    category=pattern.category,
                    severity=self._category_to_severity(pattern.category),
                )
        
        # No pattern matched - unknown failure
        self._category_counts[FailureCategory.UNKNOWN] += 1
        
        self._failure_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": failure.agent,
            "category": FailureCategory.UNKNOWN.value,
            "pattern": None,
            "message": failure.error_message[:200],
        })
        
        return FailureAnalysis(
            known_issue=False,
            root_cause=failure.error_message[:200],
            recommended_fix="Review logs and retry",
            pattern=None,
            confidence=0.5,
            category=FailureCategory.UNKNOWN,
            severity=FailureSeverity.MEDIUM,
        )

    def _category_to_severity(self, category: FailureCategory) -> FailureSeverity:
        """Map failure category to severity level."""
        severity_map = {
            FailureCategory.SYNTAX_ERROR: FailureSeverity.MEDIUM,
            FailureCategory.LOGIC_ERROR: FailureSeverity.HIGH,
            FailureCategory.IMPORT_ERROR: FailureSeverity.MEDIUM,
            FailureCategory.TYPE_ERROR: FailureSeverity.MEDIUM,
            FailureCategory.RUNTIME_ERROR: FailureSeverity.HIGH,
            FailureCategory.TIMEOUT: FailureSeverity.MEDIUM,
            FailureCategory.API_ERROR: FailureSeverity.HIGH,
            FailureCategory.VALIDATION_ERROR: FailureSeverity.LOW,
            FailureCategory.CONFIG_ERROR: FailureSeverity.MEDIUM,
            FailureCategory.DEPENDENCY_ERROR: FailureSeverity.HIGH,
            FailureCategory.UNKNOWN: FailureSeverity.MEDIUM,
        }
        return severity_map.get(category, FailureSeverity.MEDIUM)

    def get_failure_stats(self) -> Dict[str, Any]:
        """Get comprehensive failure statistics."""
        total = len(self._failure_history)
        if total == 0:
            return {"total_failures": 0}

        return {
            "total_failures": total,
            "failures_by_agent": dict(self._agent_failure_counts),
            "failures_by_category": {k.value: v for k, v in self._category_counts.items()},
            "known_vs_unknown": {
                "known": sum(1 for p in self._patterns if p.occurrence_count > 0),
                "unknown": self._category_counts[FailureCategory.UNKNOWN],
            },
            "top_patterns": [
                {"name": p.name, "count": p.occurrence_count}
                for p in sorted(self._patterns, key=lambda x: x.occurrence_count, reverse=True)
                if p.occurrence_count > 0
            ][:5],
        }

    def get_recommendations_for_agent(self, agent: str) -> List[str]:
        """Get improvement recommendations for an agent based on failure history."""
        agent_failures = [f for f in self._failure_history if f.get("agent") == agent]
        
        if not agent_failures:
            return []

        category_counts = defaultdict(int)
        for failure in agent_failures:
            category_counts[failure.get("category", "unknown")] += 1

        recommendations = []
        
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            if category == FailureCategory.SYNTAX_ERROR.value:
                recommendations.append("Add pre-execution syntax validation")
            elif category == FailureCategory.IMPORT_ERROR.value:
                recommendations.append("Implement dependency checking before execution")
            elif category == FailureCategory.LOGIC_ERROR.value:
                recommendations.append("Add more comprehensive test coverage")
            elif category == FailureCategory.TIMEOUT.value:
                recommendations.append("Optimize performance or increase timeout thresholds")
            elif category == FailureCategory.API_ERROR.value:
                recommendations.append("Add retry logic with exponential backoff")

        return recommendations[:5]


class PatternMatcher:
    """
    Standalone pattern matcher for failure messages.

    Thin wrapper around FailureAnalyzer's patterns that provides
    a synchronous ``match(error_msg) -> Optional[FailurePattern]`` API.
    """

    def __init__(self) -> None:
        self._analyzer = FailureAnalyzer()

    def match(self, error_msg: str) -> Optional[FailurePattern]:
        """Return the first FailurePattern whose symptoms match the error, or None."""
        msg = error_msg.lower()
        for pattern in self._analyzer._patterns:
            if any(symptom.lower() in msg for symptom in pattern.symptoms):
                return pattern
        return None

    def match_all(self, error_msg: str) -> List[FailurePattern]:
        """Return all patterns whose symptoms match the error (ordered by confidence)."""
        msg = error_msg.lower()
        matched = [
            p for p in self._analyzer._patterns
            if any(s.lower() in msg for s in p.symptoms)
        ]
        return sorted(matched, key=lambda p: p.confidence, reverse=True)
