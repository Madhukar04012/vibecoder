"""
Pytest configuration for backend tests.
Adds project root to sys.path so 'backend' package resolves when running from repo root.
"""
import sys
from pathlib import Path

# Project root (parent of backend/)
_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
