"""
Diff Engine — Phase 2

Generates diffs for file changes.
No auto-writes. User must approve diffs before commit.

Features:
- Unified diff generation
- Line-by-line comparison
- Context lines for clarity

Usage:
    diff = generate_diff(old_content, new_content)
    print(diff)  # Shows unified diff format
"""

import difflib
from typing import List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class DiffType(Enum):
    """Types of diff lines."""
    ADDITION = "add"
    DELETION = "remove"
    CONTEXT = "context"
    HEADER = "header"


@dataclass
class DiffLine:
    """A single line in a diff."""
    type: DiffType
    content: str
    old_line_num: Optional[int] = None
    new_line_num: Optional[int] = None


@dataclass
class FileDiff:
    """Complete diff for a file."""
    file_path: str
    old_content: str
    new_content: str
    is_new_file: bool
    is_deleted: bool
    lines: List[DiffLine]
    unified: str  # Unified diff string
    additions: int = 0
    deletions: int = 0


class DiffEngine:
    """
    Generates and manages file diffs.
    
    Human-in-the-loop: diffs must be reviewed before applying.
    """
    
    def __init__(self, context_lines: int = 3):
        """
        Initialize the diff engine.
        
        Args:
            context_lines: Number of context lines around changes
        """
        self.context_lines = context_lines
    
    def generate_diff(
        self,
        old_content: str,
        new_content: str,
        file_path: str = "",
    ) -> FileDiff:
        """
        Generate a diff between old and new content.
        
        Args:
            old_content: Original file content
            new_content: Modified file content
            file_path: Path to the file (for display)
            
        Returns:
            FileDiff with detailed diff information
        """
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        # Generate unified diff
        unified_diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}" if file_path else "a/file",
            tofile=f"b/{file_path}" if file_path else "b/file",
            lineterm="",
        )
        unified_str = "".join(unified_diff)
        
        # Parse into structured lines
        diff_lines = self._parse_diff_lines(old_content, new_content)
        
        # Count additions and deletions
        additions = sum(1 for line in diff_lines if line.type == DiffType.ADDITION)
        deletions = sum(1 for line in diff_lines if line.type == DiffType.DELETION)
        
        return FileDiff(
            file_path=file_path,
            old_content=old_content,
            new_content=new_content,
            is_new_file=old_content == "",
            is_deleted=new_content == "",
            lines=diff_lines,
            unified=unified_str,
            additions=additions,
            deletions=deletions,
        )
    
    def _parse_diff_lines(
        self,
        old_content: str,
        new_content: str,
    ) -> List[DiffLine]:
        """Parse content into structured diff lines."""
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        
        diff_lines: List[DiffLine] = []
        
        # Use SequenceMatcher for detailed comparison
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for idx, line in enumerate(old_lines[i1:i2]):
                    diff_lines.append(DiffLine(
                        type=DiffType.CONTEXT,
                        content=line,
                        old_line_num=i1 + idx + 1,
                        new_line_num=j1 + idx + 1,
                    ))
            elif tag == "delete":
                for idx, line in enumerate(old_lines[i1:i2]):
                    diff_lines.append(DiffLine(
                        type=DiffType.DELETION,
                        content=line,
                        old_line_num=i1 + idx + 1,
                    ))
            elif tag == "insert":
                for idx, line in enumerate(new_lines[j1:j2]):
                    diff_lines.append(DiffLine(
                        type=DiffType.ADDITION,
                        content=line,
                        new_line_num=j1 + idx + 1,
                    ))
            elif tag == "replace":
                # Show deletions first, then additions
                for idx, line in enumerate(old_lines[i1:i2]):
                    diff_lines.append(DiffLine(
                        type=DiffType.DELETION,
                        content=line,
                        old_line_num=i1 + idx + 1,
                    ))
                for idx, line in enumerate(new_lines[j1:j2]):
                    diff_lines.append(DiffLine(
                        type=DiffType.ADDITION,
                        content=line,
                        new_line_num=j1 + idx + 1,
                    ))
        
        return diff_lines
    
    def apply_diff(
        self,
        original_content: str,
        new_content: str,
    ) -> str:
        """
        Apply a diff (just returns new content).
        
        In production, this would handle patch application.
        For now, it's a simple replacement.
        
        Args:
            original_content: Original file content
            new_content: New content to apply
            
        Returns:
            The new content
        """
        return new_content
    
    def get_summary(self, diff: FileDiff) -> str:
        """
        Get a human-readable summary of a diff.
        
        Args:
            diff: The file diff
            
        Returns:
            Summary string
        """
        if diff.is_new_file:
            return f"[NEW] {diff.file_path} (+{diff.additions} lines)"
        elif diff.is_deleted:
            return f"[DELETE] {diff.file_path} (-{diff.deletions} lines)"
        else:
            return f"[MODIFY] {diff.file_path} (+{diff.additions} -{diff.deletions})"


# ─── Global Instance ─────────────────────────────────────────────────────────

_engine: Optional[DiffEngine] = None


def get_diff_engine() -> DiffEngine:
    """Get the global diff engine instance."""
    global _engine
    if _engine is None:
        _engine = DiffEngine()
    return _engine


def generate_diff(
    old_content: str,
    new_content: str,
    file_path: str = "",
) -> FileDiff:
    """
    Convenience function to generate a diff.
    
    Args:
        old_content: Original content
        new_content: Modified content
        file_path: File path for display
        
    Returns:
        FileDiff object
    """
    engine = get_diff_engine()
    return engine.generate_diff(old_content, new_content, file_path)
