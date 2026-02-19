"""
Comprehensive test suite for the Society system.

Tests all Phase 2 and Phase 3 components including:
- Reflection system
- Failure analyzer
- Auto-fix agent
- Model selector
- Multi-project orchestrator
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

# Import all components
from backend.core.reflection.reflection_system import (
    ReflectionAgent, Reflection, ReflectionOutcome, SelfImprovingAgentMixin
)
from backend.core.learning.failure_analyzer import (
    FailureAnalyzer, ExecutionFailure, FailureAnalysis, 
    FailureCategory, FailureSeverity, FailurePattern
)
from backend.agents.auto_fixer import AutoFixAgent, FixResult, FixStatus
from backend.core.optimization.model_selector import SmartModelSelector, ModelTier
from backend.core.orchestration.multi_project_orchestrator import (
    MultiProjectOrchestrator, Project, ProjectStatus
)
from backend.core.observability.prometheus_metrics import PrometheusMetrics


# ============================================================================
# Reflection System Tests
# ============================================================================

class TestReflectionAgent:
    """Tests for the Reflection Agent."""

    @pytest.fixture
    def reflection_agent(self):
        return ReflectionAgent()

    @pytest.mark.asyncio
    async def test_reflect_on_success(self, reflection_agent):
        """Test reflection on successful execution."""
        reflection = await reflection_agent.reflect_on_execution(
            agent_name="test_agent",
            task_description="Generate a PRD",
            outcome=ReflectionOutcome.SUCCESS,
            output={"status": "success"},
        )
        
        assert reflection.agent_name == "test_agent"
        assert reflection.outcome == ReflectionOutcome.SUCCESS
        assert len(reflection.what_went_well) > 0
        assert reflection.confidence_score > 0

    @pytest.mark.asyncio
    async def test_reflect_on_failure(self, reflection_agent):
        """Test reflection on failed execution."""
        reflection = await reflection_agent.reflect_on_execution(
            agent_name="test_agent",
            task_description="Generate code",
            outcome=ReflectionOutcome.FAILURE,
            output=None,
            error="Syntax error",
        )
        
        assert reflection.outcome == ReflectionOutcome.FAILURE
        assert len(reflection.what_went_wrong) > 0
        assert len(reflection.specific_improvements) > 0

    def test_get_reflections_for_agent(self, reflection_agent):
        """Test retrieving reflections for specific agent."""
        # Create some mock reflections
        reflection_agent.reflection_history = [
            Reflection(
                agent_name="agent_a",
                task_description="task 1",
                outcome=ReflectionOutcome.SUCCESS,
                what_went_well=["good"],
                what_went_wrong=[],
                root_cause_analysis="test",
                specific_improvements=[],
                patterns_learned=[],
            ),
            Reflection(
                agent_name="agent_b",
                task_description="task 2",
                outcome=ReflectionOutcome.SUCCESS,
                what_went_well=["good"],
                what_went_wrong=[],
                root_cause_analysis="test",
                specific_improvements=[],
                patterns_learned=[],
            ),
        ]
        
        agent_a_reflections = reflection_agent.get_reflections_for_agent("agent_a")
        assert len(agent_a_reflections) == 1
        assert agent_a_reflections[0].agent_name == "agent_a"


# ============================================================================
# Failure Analyzer Tests
# ============================================================================

class TestFailureAnalyzer:
    """Tests for the Failure Analyzer."""

    @pytest.fixture
    def failure_analyzer(self):
        return FailureAnalyzer()

    @pytest.mark.asyncio
    async def test_analyze_timeout_error(self, failure_analyzer):
        """Test analyzing a timeout error."""
        failure = ExecutionFailure(
            stage="execution",
            agent="test_agent",
            error_message="Request timeout after 30 seconds",
            stack_trace="",
        )
        
        analysis = await failure_analyzer.analyze_failure(failure)
        
        assert analysis.known_issue is True
        assert analysis.category == FailureCategory.TIMEOUT
        assert "timeout" in analysis.recommended_fix.lower()

    @pytest.mark.asyncio
    async def test_analyze_json_error(self, failure_analyzer):
        """Test analyzing a JSON parse error."""
        failure = ExecutionFailure(
            stage="parsing",
            agent="test_agent",
            error_message="Invalid JSON: Expecting property name",
            stack_trace="",
        )
        
        analysis = await failure_analyzer.analyze_failure(failure)
        
        assert analysis.known_issue is True
        assert analysis.category == FailureCategory.SYNTAX_ERROR
        assert "json" in analysis.recommended_fix.lower()

    @pytest.mark.asyncio
    async def test_analyze_unknown_error(self, failure_analyzer):
        """Test analyzing an unknown error."""
        failure = ExecutionFailure(
            stage="execution",
            agent="test_agent",
            error_message="Something weird happened",
            stack_trace="",
        )
        
        analysis = await failure_analyzer.analyze_failure(failure)
        
        assert analysis.known_issue is False
        assert analysis.category == FailureCategory.UNKNOWN

    def test_get_failure_stats_empty(self, failure_analyzer):
        """Test getting stats with no failures."""
        stats = failure_analyzer.get_failure_stats()
        assert stats["total_failures"] == 0

    @pytest.mark.asyncio
    async def test_get_failure_stats_with_data(self, failure_analyzer):
        """Test getting stats with failure data."""
        # Add some failures
        for i in range(3):
            failure = ExecutionFailure(
                stage="execution",
                agent=f"agent_{i % 2}",
                error_message="timeout" if i == 0 else "json error",
                stack_trace="",
            )
            await failure_analyzer.analyze_failure(failure)
        
        stats = failure_analyzer.get_failure_stats()
        assert stats["total_failures"] == 3
        assert "agent_0" in stats["failures_by_agent"]
        assert "agent_1" in stats["failures_by_agent"]


# ============================================================================
# Auto-Fix Agent Tests
# ============================================================================

class TestAutoFixAgent:
    """Tests for the Auto-Fix Agent."""

    @pytest.fixture
    def auto_fix_agent(self):
        return AutoFixAgent(
            name="auto_fixer",
            message_bus=Mock(),
            document_store=Mock(),
        )

    @pytest.mark.asyncio
    async def test_fix_issue_syntax_error(self, auto_fix_agent):
        """Test fixing a syntax error."""
        issue = {
            "description": "Syntax error in code",
            "error_message": "IndentationError: unexpected indent",
            "stage": "execution",
            "agent": "coder",
        }
        
        # Mock code document
        code_doc = Mock()
        code_doc.content = "def test():\n    pass"
        auto_fix_agent.document_store.get.return_value = code_doc
        
        result = await auto_fix_agent.fix_issue(issue, code_doc_id="doc_123")
        
        assert isinstance(result, FixResult)
        assert result.total_attempts > 0

    def test_determine_fix_strategy(self, auto_fix_agent):
        """Test fix strategy selection."""
        from backend.core.learning.failure_analyzer import FailureAnalysis
        
        analysis = FailureAnalysis(
            known_issue=True,
            category=FailureCategory.SYNTAX_ERROR,
            severity=FailureSeverity.MEDIUM,
            root_cause="Indentation error",
            recommended_fix="Fix indentation",
            confidence=0.9,
        )
        
        strategy = auto_fix_agent._determine_fix_strategy(analysis, attempt=1)
        assert "syntax" in strategy.lower() or "indentation" in strategy.lower()


# ============================================================================
# Model Selector Tests
# ============================================================================

class TestSmartModelSelector:
    """Tests for the Smart Model Selector."""

    @pytest.fixture
    def selector(self):
        return SmartModelSelector()

    @pytest.mark.asyncio
    async def test_select_model_simple_task(self, selector):
        """Test model selection for simple task."""
        model = await selector.select_model(
            task_description="Format this text and extract names",
            min_quality_score=0.7,
        )
        
        # Should select cheaper model for simple task
        assert model in ["claude-3-haiku", "gpt-3.5-turbo"]

    @pytest.mark.asyncio
    async def test_select_model_complex_task(self, selector):
        """Test model selection for complex task."""
        model = await selector.select_model(
            task_description="Architect a complex distributed system with microservices",
            min_quality_score=0.9,
        )
        
        # Should select premium model for complex task
        assert model in ["claude-3-opus", "gpt-4"]

    @pytest.mark.asyncio
    async def test_select_model_with_budget(self, selector):
        """Test model selection with budget constraint."""
        model = await selector.select_model(
            task_description="Generate some code",
            budget_constraint=0.01,  # Very tight budget
        )
        
        # Should select cheapest option
        assert model in ["claude-3-haiku"]

    def test_record_usage(self, selector):
        """Test recording model usage."""
        result = selector.record_usage(
            model_name="claude-3-sonnet",
            input_tokens=1000,
            output_tokens=500,
            quality_score=0.9,
        )
        
        assert result["model"] == "claude-3-sonnet"
        assert result["cost"] > 0
        assert result["input_tokens"] == 1000

    def test_get_cost_report(self, selector):
        """Test getting cost report."""
        # Add some usage
        selector.record_usage("claude-3-sonnet", 1000, 500)
        selector.record_usage("claude-3-haiku", 2000, 1000)
        
        report = selector.get_cost_report()
        
        assert report["total_cost_usd"] > 0
        assert "by_model" in report
        assert "savings_vs_premium" in report
        assert report["total_calls"] == 2


# ============================================================================
# Multi-Project Orchestrator Tests
# ============================================================================

class TestMultiProjectOrchestrator:
    """Tests for the Multi-Project Orchestrator."""

    @pytest.fixture
    async def orchestrator(self):
        orch = MultiProjectOrchestrator(max_concurrent=2, max_queue_size=10)
        await orch.start()
        yield orch
        await orch.stop()

    @pytest.mark.asyncio
    async def test_submit_project(self, orchestrator):
        """Test submitting a project."""
        project_id = await orchestrator.submit_project(
            user_idea="Build a todo app",
        )
        
        assert project_id.startswith("proj_")
        assert project_id in orchestrator._projects
        
        project = orchestrator.get_project(project_id)
        assert project.status == ProjectStatus.QUEUED

    @pytest.mark.asyncio
    async def test_get_project_status(self, orchestrator):
        """Test getting project status."""
        project_id = await orchestrator.submit_project("Test idea")
        
        status = orchestrator.get_project_status(project_id)
        assert status is not None
        assert status["project_id"] == project_id
        assert status["status"] == "queued"

    @pytest.mark.asyncio
    async def test_list_projects(self, orchestrator):
        """Test listing projects."""
        # Submit multiple projects
        for i in range(3):
            await orchestrator.submit_project(f"Project {i}")
        
        projects = orchestrator.list_projects()
        assert len(projects) == 3

    def test_get_stats_empty(self, orchestrator):
        """Test getting stats with no projects."""
        stats = orchestrator.get_stats()
        
        assert stats["total_projects"] == 0
        assert stats["active_projects"] == 0
        assert stats["completed"] == 0

    def test_get_health(self, orchestrator):
        """Test getting health status."""
        health = orchestrator.get_health()
        
        assert "status" in health
        assert health["running"] is True
        assert "queue_utilization" in health


# ============================================================================
# Prometheus Metrics Tests
# ============================================================================

class TestPrometheusMetrics:
    """Tests for Prometheus Metrics."""

    @pytest.fixture
    def metrics(self):
        return PrometheusMetrics()

    def test_record_agent_execution(self, metrics):
        """Test recording agent execution."""
        metrics.record_agent_execution(
            agent_name="test_agent",
            status="success",
            duration_seconds=1.5,
        )
        
        # Should not raise error
        assert True

    def test_record_token_usage(self, metrics):
        """Test recording token usage."""
        metrics.record_token_usage(
            agent_name="test_agent",
            model="claude-3-sonnet",
            input_tokens=1000,
            output_tokens=500,
        )
        
        # Should not raise error
        assert True

    def test_update_active_runs(self, metrics):
        """Test updating active runs gauge."""
        metrics.update_active_runs(5)
        
        # Should not raise error
        assert True

    def test_get_metrics(self, metrics):
        """Test getting metrics in Prometheus format."""
        data = metrics.get_metrics()
        
        # Should return bytes
        assert isinstance(data, bytes)


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_full_workflow_integration():
    """Test the full workflow with all components."""
    # This would test the integration of all components
    # For now, just verify imports work
    
    from backend.core.reflection.reflection_system import ReflectionAgent
    from backend.core.learning.failure_analyzer import FailureAnalyzer
    from backend.agents.auto_fixer import AutoFixAgent
    from backend.core.optimization.model_selector import SmartModelSelector
    from backend.core.orchestration.multi_project_orchestrator import MultiProjectOrchestrator
    from backend.core.observability.prometheus_metrics import PrometheusMetrics
    
    # Create instances
    reflection = ReflectionAgent()
    failure_analyzer = FailureAnalyzer()
    model_selector = SmartModelSelector()
    metrics = PrometheusMetrics()
    
    # Verify they exist
    assert reflection is not None
    assert failure_analyzer is not None
    assert model_selector is not None
    assert metrics is not None


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.asyncio
async def test_concurrent_projects():
    """Test handling multiple projects concurrently."""
    orchestrator = MultiProjectOrchestrator(max_concurrent=3)
    await orchestrator.start()
    
    try:
        # Submit multiple projects
        project_ids = []
        for i in range(5):
            pid = await orchestrator.submit_project(f"Project {i}")
            project_ids.append(pid)
        
        # Verify all submitted
        assert len(project_ids) == 5
        
        # Wait a bit for processing
        await asyncio.sleep(0.1)
        
        # Check stats
        stats = orchestrator.get_stats()
        assert stats["total_projects"] == 5
        
    finally:
        await orchestrator.stop()


def test_failure_pattern_matching():
    """Test failure pattern matching performance."""
    from backend.core.learning.failure_analyzer import PatternMatcher
    
    matcher = PatternMatcher()
    
    # Test matching
    error = "IndentationError: unexpected indent at line 42"
    pattern = matcher.match(error)
    
    assert pattern is not None
    assert "indentation" in pattern.name.lower()
