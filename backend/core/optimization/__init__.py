"""Optimization module for cost and performance tuning."""

from backend.core.optimization.model_selector import (
    SmartModelSelector,
    ModelTier,
    ModelInfo,
    get_model_selector,
)

__all__ = [
    "SmartModelSelector",
    "ModelTier",
    "ModelInfo", 
    "get_model_selector",
]