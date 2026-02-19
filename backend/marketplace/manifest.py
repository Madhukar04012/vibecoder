"""
Atom Manifest Parser — Phase 6

Parses atom.yaml manifests with capability-based security.

Manifest Format:
    id: "security-auditor-atom"
    version: "1.0.0"
    author: "VibeDev"
    entrypoint: "auditor.wasm"
    
    capabilities:
      read_files: ["src/**/*.py"]
      write_files: ["audit_report.md"]
      network_access: ["api.osv.dev"]
      terminal_access: false
    
    role: "Security Engineer"
    system_prompt: "You are a specialized security auditor..."

Usage:
    manifest = AtomManifest.from_file("path/to/atom.yaml")
    if manifest.validate():
        approved = manifest.request_approval(capabilities)
"""

import yaml
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


# ─── Capability Types ────────────────────────────────────────────────────────

class CapabilityType(Enum):
    READ_FILES = "read_files"
    WRITE_FILES = "write_files"
    NETWORK_ACCESS = "network_access"
    TERMINAL_ACCESS = "terminal_access"
    ENV_ACCESS = "env_access"
    DATABASE_ACCESS = "database_access"
    AGENT_COMMUNICATION = "agent_communication"


# ─── Risk Levels ─────────────────────────────────────────────────────────────

class RiskLevel(Enum):
    LOW = "low"  # Read-only, scoped
    MEDIUM = "medium"  # Write access, limited network
    HIGH = "high"  # Terminal, env, database
    CRITICAL = "critical"  # Unrestricted access


# Capability risk mapping
CAPABILITY_RISKS: Dict[CapabilityType, RiskLevel] = {
    CapabilityType.READ_FILES: RiskLevel.LOW,
    CapabilityType.WRITE_FILES: RiskLevel.MEDIUM,
    CapabilityType.NETWORK_ACCESS: RiskLevel.MEDIUM,
    CapabilityType.TERMINAL_ACCESS: RiskLevel.HIGH,
    CapabilityType.ENV_ACCESS: RiskLevel.CRITICAL,
    CapabilityType.DATABASE_ACCESS: RiskLevel.HIGH,
    CapabilityType.AGENT_COMMUNICATION: RiskLevel.LOW,
}


# ─── Capability Set ──────────────────────────────────────────────────────────

@dataclass
class CapabilitySet:
    """Validated set of capabilities for an atom."""
    read_files: List[str] = field(default_factory=list)
    write_files: List[str] = field(default_factory=list)
    network_access: List[str] = field(default_factory=list)
    terminal_access: bool = False
    env_access: List[str] = field(default_factory=list)
    database_access: bool = False
    agent_communication: bool = True  # Default allowed
    
    def get_risk_level(self) -> RiskLevel:
        """Calculate overall risk level."""
        if self.env_access:
            return RiskLevel.CRITICAL
        if self.terminal_access or self.database_access:
            return RiskLevel.HIGH
        if self.write_files or self.network_access:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "read_files": self.read_files,
            "write_files": self.write_files,
            "network_access": self.network_access,
            "terminal_access": self.terminal_access,
            "env_access": self.env_access,
            "database_access": self.database_access,
            "agent_communication": self.agent_communication,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CapabilitySet":
        return cls(
            read_files=data.get("read_files", []),
            write_files=data.get("write_files", []),
            network_access=data.get("network_access", []),
            terminal_access=data.get("terminal_access", False),
            env_access=data.get("env_access", []),
            database_access=data.get("database_access", False),
            agent_communication=data.get("agent_communication", True),
        )


# ─── Atom Manifest ───────────────────────────────────────────────────────────

@dataclass
class AtomManifest:
    """
    Parsed atom.yaml manifest with validation.
    
    Attributes:
        id: Unique atom identifier
        version: Semantic version
        author: Author name/handle
        entrypoint: WASM file path
        capabilities: Requested capabilities
        role: Agent role name
        system_prompt: Agent system prompt
    """
    id: str
    version: str
    author: str
    entrypoint: str
    capabilities: CapabilitySet
    role: str = "Assistant"
    system_prompt: str = ""
    description: str = ""
    homepage: str = ""
    license: str = "MIT"
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    # Validation state
    _valid: bool = False
    _errors: List[str] = field(default_factory=list)
    
    @classmethod
    def from_file(cls, path: str) -> "AtomManifest":
        """Load and parse atom.yaml."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AtomManifest":
        """Create manifest from dict."""
        capabilities = CapabilitySet.from_dict(data.get("capabilities", {}))
        
        return cls(
            id=data.get("id", "unknown"),
            version=data.get("version", "0.0.0"),
            author=data.get("author", "Unknown"),
            entrypoint=data.get("entrypoint", ""),
            capabilities=capabilities,
            role=data.get("role", "Assistant"),
            system_prompt=data.get("system_prompt", ""),
            description=data.get("description", ""),
            homepage=data.get("homepage", ""),
            license=data.get("license", "MIT"),
            tags=data.get("tags", []),
            dependencies=data.get("dependencies", []),
        )
    
    def validate(self) -> bool:
        """
        Validate manifest integrity.
        
        Returns:
            True if valid
        """
        self._errors = []
        
        # Required fields
        if not self.id:
            self._errors.append("Missing required field: id")
        elif not re.match(r"^[a-z0-9-]+$", self.id):
            self._errors.append("Invalid id format (must be lowercase alphanumeric with hyphens)")
        
        if not self.version:
            self._errors.append("Missing required field: version")
        elif not re.match(r"^\d+\.\d+\.\d+", self.version):
            self._errors.append("Invalid version format (must be semver)")
        
        if not self.entrypoint:
            self._errors.append("Missing required field: entrypoint")
        elif not self.entrypoint.endswith(".wasm"):
            self._errors.append("Entrypoint must be a .wasm file")
        
        # Validate capabilities
        self._validate_capabilities()
        
        self._valid = len(self._errors) == 0
        return self._valid
    
    def _validate_capabilities(self) -> None:
        """Validate capability patterns."""
        # Validate file patterns
        for pattern in self.capabilities.read_files + self.capabilities.write_files:
            if ".." in pattern:
                self._errors.append(f"Invalid path pattern (no parent traversal): {pattern}")
            if pattern.startswith("/"):
                self._errors.append(f"Invalid path pattern (no absolute paths): {pattern}")
        
        # Validate network patterns
        for host in self.capabilities.network_access:
            if not re.match(r"^[a-zA-Z0-9.-]+$", host):
                self._errors.append(f"Invalid network host: {host}")
        
        # Validate env access
        for env_var in self.capabilities.env_access:
            if env_var.upper() in {"PATH", "HOME", "USER", "SHELL"}:
                self._errors.append(f"System env var not allowed: {env_var}")
    
    def get_risk_level(self) -> RiskLevel:
        """Get overall risk level for this atom."""
        return self.capabilities.get_risk_level()
    
    def get_errors(self) -> List[str]:
        """Get validation errors."""
        return self._errors
    
    def is_valid(self) -> bool:
        """Check if manifest is valid."""
        return self._valid
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for storage/API."""
        return {
            "id": self.id,
            "version": self.version,
            "author": self.author,
            "entrypoint": self.entrypoint,
            "capabilities": self.capabilities.to_dict(),
            "role": self.role,
            "system_prompt": self.system_prompt,
            "description": self.description,
            "homepage": self.homepage,
            "license": self.license,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "risk_level": self.get_risk_level().value,
        }
    
    def to_yaml(self) -> str:
        """Serialize back to YAML."""
        return yaml.dump(self.to_dict(), default_flow_style=False)


# ─── Capability Approval Request ─────────────────────────────────────────────

@dataclass
class CapabilityApproval:
    """Request for user approval of atom capabilities."""
    atom_id: str
    capabilities: CapabilitySet
    risk_level: RiskLevel
    approved: bool = False
    approved_by: str = ""
    approved_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "atom_id": self.atom_id,
            "capabilities": self.capabilities.to_dict(),
            "risk_level": self.risk_level.value,
            "approved": self.approved,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
        }


# ─── Convenience Functions ───────────────────────────────────────────────────

def parse_manifest(path: str) -> AtomManifest:
    """Parse and validate an atom manifest."""
    manifest = AtomManifest.from_file(path)
    manifest.validate()
    return manifest


def create_sample_manifest() -> str:
    """Create sample atom.yaml content."""
    return """# VibeCoder Atom Manifest
id: "my-custom-atom"
version: "1.0.0"
author: "YourName"
entrypoint: "agent.wasm"

description: "A custom atom for VibeCoder"
homepage: "https://github.com/you/my-atom"
license: "MIT"
tags: ["utility", "automation"]

# Capability-Based Security (Engine-Enforced)
capabilities:
  read_files:
    - "src/**/*.py"
    - "**/*.md"
  write_files:
    - "output/**/*"
  network_access: []
  terminal_access: false
  env_access: []
  database_access: false

# Agent Definition
role: "Custom Assistant"
system_prompt: |
  You are a helpful custom assistant.
  Your role is to assist with specific tasks.
"""
