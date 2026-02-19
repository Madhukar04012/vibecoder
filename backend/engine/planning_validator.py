"""
Planning Validator — Phase-1

Validates PRD and Roadmap outputs contain required sections.
Planning MUST pass validation before moving to EXECUTION.

Usage:
    from engine.planning_validator import validate_planning_output
    
    validate_planning_output(prd_text, roadmap_text)  # Raises ValueError if invalid
"""

from typing import List, Tuple
from dataclasses import dataclass


# Required sections for PRD
REQUIRED_PRD_SECTIONS = [
    "Problem",
    "Scope",
    "User Flow",
    "Acceptance Criteria",
    "Constraints",
]

# Alternative keywords that satisfy each PRD section
PRD_SECTION_ALIASES = {
    "Problem": ["problem", "objective", "goal", "purpose", "overview"],
    "Scope": ["scope", "features", "functionality", "requirements"],
    "User Flow": ["user flow", "user story", "user stories", "workflow", "user journey"],
    "Acceptance Criteria": ["acceptance criteria", "success criteria", "criteria", "requirements"],
    "Constraints": ["constraints", "limitations", "restrictions", "tech hints", "technical"],
}

# Required sections for Roadmap
REQUIRED_ROADMAP_SECTIONS = [
    "Architecture",
    "Modules",
    "Data Flow",
    "Risks",
    "Milestones",
]

# Alternative keywords for Roadmap
ROADMAP_SECTION_ALIASES = {
    "Architecture": ["architecture", "stack", "structure", "design", "directory"],
    "Modules": ["modules", "components", "files", "directory_structure", "component_tree"],
    "Data Flow": ["data flow", "data model", "api", "endpoints", "api_endpoints"],
    "Risks": ["risks", "challenges", "concerns", "issues"],
    "Milestones": ["milestones", "phases", "timeline", "schedule", "steps"],
}


@dataclass
class ValidationResult:
    """Result of a validation check."""
    valid: bool
    missing: List[str]
    found: List[str]
    warnings: List[str]
    
    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "missing": self.missing,
            "found": self.found,
            "warnings": self.warnings,
        }


def _check_section(text: str, section: str, aliases: List[str]) -> bool:
    """Check if any alias for a section exists in the text."""
    text_lower = text.lower()
    return any(alias in text_lower for alias in aliases)


def _normalize_content(content) -> str:
    """Convert dict/list/str to searchable string."""
    if isinstance(content, dict):
        import json
        return json.dumps(content, indent=2).lower()
    elif isinstance(content, list):
        import json
        return json.dumps(content, indent=2).lower()
    elif content is None:
        return ""
    return str(content).lower()


def validate_prd(prd) -> ValidationResult:
    """
    Validate that a PRD contains all required sections.
    
    Args:
        prd: PRD content (str or dict)
        
    Returns:
        ValidationResult with details
    """
    text = _normalize_content(prd)
    
    missing = []
    found = []
    warnings = []
    
    for section in REQUIRED_PRD_SECTIONS:
        aliases = PRD_SECTION_ALIASES.get(section, [section.lower()])
        if _check_section(text, section, aliases):
            found.append(section)
        else:
            missing.append(section)
    
    # Check for empty content
    if len(text) < 50:
        warnings.append("PRD content seems too short")
    
    return ValidationResult(
        valid=len(missing) == 0,
        missing=missing,
        found=found,
        warnings=warnings,
    )


def validate_roadmap(roadmap) -> ValidationResult:
    """
    Validate that a Roadmap contains all required sections.
    
    Args:
        roadmap: Roadmap content (str or dict)
        
    Returns:
        ValidationResult with details
    """
    text = _normalize_content(roadmap)
    
    missing = []
    found = []
    warnings = []
    
    for section in REQUIRED_ROADMAP_SECTIONS:
        aliases = ROADMAP_SECTION_ALIASES.get(section, [section.lower()])
        if _check_section(text, section, aliases):
            found.append(section)
        else:
            missing.append(section)
    
    # Check for empty content
    if len(text) < 50:
        warnings.append("Roadmap content seems too short")
    
    return ValidationResult(
        valid=len(missing) == 0,
        missing=missing,
        found=found,
        warnings=warnings,
    )


def validate_planning_output(prd, roadmap) -> Tuple[ValidationResult, ValidationResult]:
    """
    Validate both PRD and Roadmap.
    
    Args:
        prd: PRD content
        roadmap: Roadmap/Architecture content
        
    Returns:
        Tuple of (prd_result, roadmap_result)
        
    Raises:
        ValueError: If critical sections are missing
    """
    prd_result = validate_prd(prd)
    roadmap_result = validate_roadmap(roadmap)
    
    # Collect critical missing sections
    critical_missing = []
    
    # PRD must have at least Problem and Scope
    if "Problem" in prd_result.missing and "Scope" in prd_result.missing:
        critical_missing.append("PRD missing both Problem and Scope")
    
    # Roadmap must have at least Architecture and Modules
    if "Architecture" in roadmap_result.missing and "Modules" in roadmap_result.missing:
        critical_missing.append("Roadmap missing both Architecture and Modules")
    
    if critical_missing:
        raise ValueError(f"Planning validation failed: {'; '.join(critical_missing)}")
    
    return prd_result, roadmap_result


def get_validation_summary(prd, roadmap) -> dict:
    """
    Get a summary of validation results for logging.
    
    Args:
        prd: PRD content
        roadmap: Roadmap content
        
    Returns:
        Summary dict with validation status
    """
    try:
        prd_result, roadmap_result = validate_planning_output(prd, roadmap)
        return {
            "status": "passed",
            "prd": prd_result.to_dict(),
            "roadmap": roadmap_result.to_dict(),
        }
    except ValueError as e:
        return {
            "status": "failed",
            "error": str(e),
        }
