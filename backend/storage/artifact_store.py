"""
Artifact persistence with versioned generations.

Stores each run's generated files, manifest, and downloadable zip bundle.
Supports local storage by default and optional S3 upload of bundles.
"""

from __future__ import annotations

import json
import os
import shutil
import zipfile
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


ARTIFACT_ROOT = Path("generated_projects") / "artifacts"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def flatten_structure(node: Dict[str, Any], prefix: str = "") -> Dict[str, str]:
    """Flatten nested file tree into path->content mapping."""
    output: Dict[str, str] = {}
    for name, value in node.items():
        path = f"{prefix}/{name}" if prefix else name
        if isinstance(value, dict):
            output.update(flatten_structure(value, path))
        elif isinstance(value, str):
            output[path] = value
    return output


@dataclass
class ArtifactManifest:
    project_key: str
    run_id: str
    version: int
    created_at: str
    file_count: int
    files: List[str]
    metadata: Dict[str, Any]
    bundle_path: str
    s3_object: str | None = None


class ArtifactStore:
    """Versioned local artifact store with optional S3 bundle upload."""

    def __init__(self, root: Path | None = None):
        self.root = root or ARTIFACT_ROOT
        self.root.mkdir(parents=True, exist_ok=True)

    def _project_dir(self, project_key: str) -> Path:
        safe = project_key.replace("/", "_").replace("..", "_")
        directory = self.root / safe
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def _next_version(self, project_key: str) -> int:
        project_dir = self._project_dir(project_key)
        versions = [
            int(path.name[1:])
            for path in project_dir.iterdir()
            if path.is_dir() and path.name.startswith("v") and path.name[1:].isdigit()
        ]
        return (max(versions) + 1) if versions else 1

    def persist(
        self,
        project_key: str,
        run_id: str,
        files: Dict[str, str] | Dict[str, Any],
        metadata: Dict[str, Any] | None = None,
        version: int | None = None,
    ) -> ArtifactManifest:
        """Persist a generation version with manifest and bundle."""
        flat_files: Dict[str, str]
        if files and all(isinstance(v, str) for v in files.values()):
            flat_files = files  # already flat mapping
        else:
            flat_files = flatten_structure(files)

        version_number = version or self._next_version(project_key)
        project_dir = self._project_dir(project_key)
        version_dir = project_dir / f"v{version_number}"
        version_dir.mkdir(parents=True, exist_ok=True)

        files_dir = version_dir / "files"
        files_dir.mkdir(parents=True, exist_ok=True)

        for rel_path, content in flat_files.items():
            target = files_dir / rel_path.replace("\\", "/")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        bundle_path = version_dir / "bundle.zip"
        with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for rel_path, content in flat_files.items():
                archive.writestr(rel_path.replace("\\", "/"), content)

        manifest = ArtifactManifest(
            project_key=project_key,
            run_id=run_id,
            version=version_number,
            created_at=_utc_now(),
            file_count=len(flat_files),
            files=sorted(flat_files.keys()),
            metadata=metadata or {},
            bundle_path=str(bundle_path),
        )

        manifest_path = version_dir / "manifest.json"
        manifest_path.write_text(json.dumps(asdict(manifest), indent=2), encoding="utf-8")

        s3_object = self._upload_bundle_if_configured(project_key, version_number, bundle_path)
        if s3_object:
            manifest.s3_object = s3_object
            manifest_path.write_text(json.dumps(asdict(manifest), indent=2), encoding="utf-8")

        return manifest

    def list_versions(self, project_key: str) -> List[Dict[str, Any]]:
        """List manifests for a project's stored versions (newest first)."""
        project_dir = self._project_dir(project_key)
        manifests: List[Dict[str, Any]] = []
        for path in project_dir.glob("v*/manifest.json"):
            try:
                manifests.append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                continue

        manifests.sort(key=lambda item: item.get("version", 0), reverse=True)
        return manifests

    def load_version(self, project_key: str, version: int) -> Dict[str, str]:
        """Load files from a stored version."""
        files_dir = self._project_dir(project_key) / f"v{version}" / "files"
        if not files_dir.exists():
            raise FileNotFoundError(f"Artifact version v{version} not found for '{project_key}'")

        data: Dict[str, str] = {}
        for path in files_dir.rglob("*"):
            if path.is_file():
                rel = path.relative_to(files_dir).as_posix()
                data[rel] = path.read_text(encoding="utf-8")
        return data

    def get_bundle_path(self, project_key: str, version: int) -> Path:
        bundle = self._project_dir(project_key) / f"v{version}" / "bundle.zip"
        if not bundle.exists():
            raise FileNotFoundError(f"Bundle not found for '{project_key}' version {version}")
        return bundle

    def clear_project(self, project_key: str) -> None:
        """Delete all stored versions for a project key."""
        directory = self._project_dir(project_key)
        if directory.exists():
            shutil.rmtree(directory, ignore_errors=True)

    def _upload_bundle_if_configured(self, project_key: str, version: int, bundle: Path) -> str | None:
        backend = os.getenv("ARTIFACT_BACKEND", "local").strip().lower()
        if backend != "s3":
            return None

        bucket = os.getenv("ARTIFACT_S3_BUCKET", "").strip()
        prefix = os.getenv("ARTIFACT_S3_PREFIX", "vibecober").strip("/")
        if not bucket:
            return None

        try:
            import boto3

            key = f"{prefix}/{project_key}/v{version}/bundle.zip"
            client = boto3.client("s3")
            client.upload_file(str(bundle), bucket, key)
            return f"s3://{bucket}/{key}"
        except Exception:
            return None


_STORE: ArtifactStore | None = None


def get_artifact_store() -> ArtifactStore:
    global _STORE
    if _STORE is None:
        _STORE = ArtifactStore()
    return _STORE
