"""
Agent output contracts for pipeline enforcement.

Each agent must return a JSON-serializable payload that validates against a
strict Pydantic model before the next agent can execute.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class AgentContractError(ValueError):
    """Raised when an agent output violates its contract."""


class StrictModel(BaseModel):
    """Base class for strict contract models."""

    model_config = ConfigDict(extra="forbid", strict=False, protected_namespaces=())


class PlannerOutputContract(StrictModel):
    project_type: str
    backend: str
    frontend: str
    database: str
    modules: List[str]


class DBSchemaColumnContract(StrictModel):
    name: str
    type: str
    nullable: bool = False
    primary_key: bool = False
    unique: bool = False
    default: str | None = None
    foreign_key: str | None = None


class DBSchemaTableContract(StrictModel):
    name: str
    columns: List[DBSchemaColumnContract]
    relationships: List[str] = Field(default_factory=list)


class DBSchemaPayloadContract(StrictModel):
    tables: List[DBSchemaTableContract]
    orm_models: bool = True
    migration_ready: bool = True


class DBSchemaOutputContract(StrictModel):
    schema_: DBSchemaPayloadContract = Field(alias="schema")
    code: str
    tables_count: int
    status: Literal["success"]


class AuthPayloadContract(StrictModel):
    strategy: Literal["jwt", "session"]
    user_model: str
    routes: List[str]
    requires_hashing: bool
    requires_env: List[str]
    files: Dict[str, str]


class AuthOutputContract(StrictModel):
    auth: AuthPayloadContract
    routes_count: int
    files_count: int
    status: Literal["success", "skipped"]


class TesterPayloadContract(StrictModel):
    framework: str
    tests: List[str]
    requires_test_db: bool
    files: Dict[str, str]


class TesterOutputContract(StrictModel):
    tests: TesterPayloadContract
    test_count: int
    files_count: int
    status: Literal["success", "skipped"]


class DeployPayloadContract(StrictModel):
    strategy: str
    includes_compose: bool
    requires_env: List[str]
    files: Dict[str, str]


class DeployOutputContract(StrictModel):
    deploy: DeployPayloadContract
    files_count: int
    status: Literal["success"]


class ReviewScoreBreakdownContract(StrictModel):
    structure: int
    code_quality: int
    security: int
    completeness: int


class ReviewScoreContract(StrictModel):
    tier: str
    total_score: int
    file_count: int
    breakdown: ReviewScoreBreakdownContract
    issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class CodeReviewerOutputContract(StrictModel):
    approved: bool
    score: ReviewScoreContract
    file_reviews: Dict[str, Dict[str, Any]]
    critical_issues: List[str]
    summary: str


CONTRACTS: Dict[str, type[BaseModel]] = {
    "planner": PlannerOutputContract,
    "db_schema": DBSchemaOutputContract,
    "auth": AuthOutputContract,
    "tester": TesterOutputContract,
    "deployer": DeployOutputContract,
    "code_reviewer": CodeReviewerOutputContract,
}


def _validate_project_structure(node: Any, path: str = "root") -> None:
    """Validate recursively that coder output is a nested file tree."""
    if isinstance(node, dict):
        for key, value in node.items():
            if not isinstance(key, str) or not key.strip():
                raise AgentContractError(f"Coder output has invalid key at '{path}'")
            _validate_project_structure(value, f"{path}/{key}")
        return

    if not isinstance(node, str):
        raise AgentContractError(
            f"Coder output leaf must be file content string at '{path}', got {type(node).__name__}"
        )


def validate_agent_output(agent_name: str, payload: Any) -> Dict[str, Any]:
    """
    Validate agent output against its contract.

    Returns normalized dict when valid.
    """
    if agent_name == "coder":
        if not isinstance(payload, dict) or not payload:
            raise AgentContractError("Coder output must be a non-empty dict")
        _validate_project_structure(payload)
        return payload

    model = CONTRACTS.get(agent_name)
    if not model:
        if not isinstance(payload, dict):
            raise AgentContractError(f"Agent '{agent_name}' output must be a dict")
        return payload

    try:
        validated = model.model_validate(payload)
    except ValidationError as exc:
        raise AgentContractError(
            f"Contract validation failed for '{agent_name}': {exc}"
        ) from exc

    return validated.model_dump(by_alias=True)
