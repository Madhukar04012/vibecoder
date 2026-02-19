"""
Code Reviewer Agent — Quality Gate

Reviews generated code against S-class standards BEFORE writing to disk.
Acts as the final quality gate in the pipeline.

Responsibilities:
1. Review generated code for quality issues
2. Score against S-class standards
3. Suggest improvements or REJECT below-threshold code
4. Ensure consistency across all generated files

Non-Responsibilities:
- Does NOT write code
- Does NOT fix code (sends back to Engineer)
- Does NOT skip reviews
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from backend.agents.base_agent import BaseAgent
from backend.standards.quality_standards import (
    score_project,
    QualityScore,
    QualityTier,
    SCLASS_FRONTEND_GUIDELINES,
    SCLASS_BACKEND_GUIDELINES,
)


@dataclass
class ReviewResult:
    """Result of a code review."""
    approved: bool
    score: QualityScore
    file_reviews: Dict[str, Dict[str, Any]]  # path -> {issues, suggestions}
    critical_issues: List[str]
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approved": self.approved,
            "score": self.score.to_dict(),
            "file_reviews": self.file_reviews,
            "critical_issues": self.critical_issues,
            "summary": self.summary,
        }


class CodeReviewerAgent(BaseAgent):
    """
    Senior Code Reviewer — Quality gate for generated projects.

    Reviews ALL generated files against S-class standards
    and produces a pass/fail verdict with detailed feedback.
    """

    name = "code_reviewer"

    # Minimum quality tier to pass review
    MIN_TIER = QualityTier.A  # Must be at least A-tier to pass

    def review(
        self,
        files: Dict[str, str],
        prd: Optional[Dict[str, Any]] = None,
    ) -> ReviewResult:
        """
        Review all generated files.

        Args:
            files: Dict mapping file paths to contents
            prd: Original PRD for context

        Returns:
            ReviewResult with approval status and detailed feedback
        """
        # 1. Automated scoring
        quality_score = score_project(files)

        # 2. Per-file review (targeted, not every file)
        file_reviews = {}
        critical_issues = []

        for path, content in files.items():
            issues = self._review_file(path, content)
            if issues["critical"]:
                critical_issues.extend(issues["critical"])
            if issues["critical"] or issues["warnings"]:
                file_reviews[path] = issues

        # 3. LLM-powered review for key files (if available)
        key_files = self._identify_key_files(files)
        for path in key_files:
            if path in files:
                llm_review = self._llm_review_file(path, files[path], prd)
                if llm_review:
                    if path not in file_reviews:
                        file_reviews[path] = {"critical": [], "warnings": [], "suggestions": []}
                    file_reviews[path]["llm_feedback"] = llm_review

        # 4. Determine approval
        approved = (
            quality_score.tier.value <= self.MIN_TIER.value
            and len(critical_issues) == 0
        )

        # 5. Build summary
        summary = self._build_summary(quality_score, critical_issues, approved)

        return ReviewResult(
            approved=approved,
            score=quality_score,
            file_reviews=file_reviews,
            critical_issues=critical_issues,
            summary=summary,
        )

    def _review_file(self, path: str, content: str) -> Dict[str, List[str]]:
        """Review a single file for common issues."""
        critical = []
        warnings = []
        suggestions = []

        # Empty or near-empty files
        if len(content.strip()) < 10:
            if not path.endswith("__init__.py") and not path.endswith(".gitkeep"):
                critical.append(f"{path}: File is empty or nearly empty")

        # Hardcoded secrets
        secret_patterns = [
            "your-secret-key", "change-in-production", "password123",
            "sk-test_", "pk_test_", "AKIA",
        ]
        for pattern in secret_patterns:
            if pattern in content:
                critical.append(f"{path}: Hardcoded secret found: '{pattern}'")

        # TODO/placeholder checks
        if content.count("TODO") > 3:
            warnings.append(f"{path}: Too many TODOs ({content.count('TODO')})")
        if "placeholder" in content.lower() and not path.endswith(".md"):
            warnings.append(f"{path}: Contains 'placeholder' text")

        # Frontend-specific checks
        if path.endswith((".tsx", ".ts", ".jsx", ".js")):
            if "any" in content and "eslint" not in path.lower():
                any_count = content.count(": any") + content.count("<any>")
                if any_count > 2:
                    warnings.append(f"{path}: {any_count} 'any' types — use proper types")

            if path.endswith((".jsx", ".js")) and "component" in path.lower():
                warnings.append(f"{path}: Should use .tsx/.ts instead of .jsx/.js")

            if "console.log" in content:
                warnings.append(f"{path}: Remove console.log before production")

        # Backend-specific checks
        if path.endswith(".py"):
            if "print(" in content and "test" not in path.lower():
                warnings.append(f"{path}: Use structured logging instead of print()")

            if "def " in content:
                # Check for type hints
                import re
                funcs = re.findall(r'def \w+\([^)]*\)', content)
                untyped = [f for f in funcs if "->" not in content[content.index(f):content.index(f) + len(f) + 30]]
                if len(untyped) > len(funcs) * 0.5 and len(funcs) > 2:
                    warnings.append(f"{path}: Many functions missing return type hints")

            if 'allow_origins=["*"]' in content:
                critical.append(f"{path}: CORS allows all origins — security risk")

        return {
            "critical": critical,
            "warnings": warnings,
            "suggestions": suggestions,
        }

    def _identify_key_files(self, files: Dict[str, str]) -> List[str]:
        """Identify the most important files to review with LLM."""
        key_files = []
        for path in files:
            if any(kw in path.lower() for kw in [
                "main", "app", "config", "security", "auth", "api-client",
                "router", "index.ts", "index.tsx",
            ]):
                key_files.append(path)
        return key_files[:5]  # Max 5 LLM reviews to control cost

    def _llm_review_file(
        self,
        path: str,
        content: str,
        prd: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Use LLM to review a key file."""
        if not content or len(content) < 50:
            return None

        is_frontend = any(path.endswith(ext) for ext in (".tsx", ".ts", ".jsx", ".js"))
        guidelines = SCLASS_FRONTEND_GUIDELINES if is_frontend else SCLASS_BACKEND_GUIDELINES

        system = f"""You are a Senior Staff Engineer conducting a code review.
Review this file against these S-class standards:

{guidelines}

Output a brief review (max 200 words) focusing on:
1. Critical issues that MUST be fixed
2. Quality rating (S/A/B/C)
3. Top 3 improvement suggestions

Be concise and actionable. No generic praise."""

        try:
            response = self.call_llm_simple(
                system=system,
                user=f"Review this file ({path}):\n\n{content[:3000]}",
                max_tokens=512,
                temperature=0.2,
            )
            return response
        except Exception:
            return None

    def _build_summary(
        self,
        score: QualityScore,
        critical_issues: List[str],
        approved: bool,
    ) -> str:
        """Build a human-readable review summary."""
        status = "APPROVED" if approved else "NEEDS REVISION"
        lines = [
            f"Code Review: {status}",
            f"Quality Tier: {score.tier.value} ({score.total_score}/100)",
            f"Files Reviewed: {score.file_count}",
            "",
            "Breakdown:",
            f"  Structure:    {score.structure_score}/25",
            f"  Code Quality: {score.code_quality_score}/25",
            f"  Security:     {score.security_score}/25",
            f"  Completeness: {score.completeness_score}/25",
        ]

        if critical_issues:
            lines.append("")
            lines.append(f"Critical Issues ({len(critical_issues)}):")
            for issue in critical_issues[:5]:
                lines.append(f"  - {issue}")

        if score.issues:
            lines.append("")
            lines.append(f"Issues ({len(score.issues)}):")
            for issue in score.issues[:5]:
                lines.append(f"  - {issue}")

        if score.recommendations:
            lines.append("")
            lines.append("Recommendations:")
            for rec in score.recommendations[:3]:
                lines.append(f"  - {rec}")

        return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═════════════════════════════════════════════════════════════════════════════

def review_code(
    files: Dict[str, str],
    prd: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Public API for orchestrator.

    Args:
        files: Generated files to review
        prd: Original product requirements

    Returns:
        Review result dict
    """
    reviewer = CodeReviewerAgent()
    result = reviewer.review(files, prd)
    return result.to_dict()
