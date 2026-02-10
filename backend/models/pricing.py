"""
Model Pricing — Phase-1

Token cost mapping for various LLM providers.

Usage:
    from models.pricing import get_model_pricing, estimate_cost
    
    pricing = get_model_pricing("gpt-4")
    cost = estimate_cost("gpt-4", input_tokens=500, output_tokens=200)
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class ModelPricing:
    """Pricing info for a single model."""
    input_cost_per_1k: float  # $/1K input tokens
    output_cost_per_1k: float  # $/1K output tokens
    provider: str
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate total cost for a request."""
        input_cost = (input_tokens / 1000) * self.input_cost_per_1k
        output_cost = (output_tokens / 1000) * self.output_cost_per_1k
        return input_cost + output_cost


# Model pricing database (as of 2026)
MODEL_PRICING: Dict[str, ModelPricing] = {
    # OpenAI
    "gpt-4": ModelPricing(0.03, 0.06, "openai"),
    "gpt-4-turbo": ModelPricing(0.01, 0.03, "openai"),
    "gpt-4o": ModelPricing(0.005, 0.015, "openai"),
    "gpt-4o-mini": ModelPricing(0.00015, 0.0006, "openai"),
    "gpt-3.5-turbo": ModelPricing(0.0005, 0.0015, "openai"),
    
    # Anthropic
    "claude-3-opus": ModelPricing(0.015, 0.075, "anthropic"),
    "claude-3-sonnet": ModelPricing(0.003, 0.015, "anthropic"),
    "claude-3-haiku": ModelPricing(0.00025, 0.00125, "anthropic"),
    "claude-3.5-sonnet": ModelPricing(0.003, 0.015, "anthropic"),
    
    # NVIDIA NIM (Llama 3.3 via API)
    "meta/llama-3.3-70b-instruct": ModelPricing(0.0008, 0.0008, "nvidia"),
    "meta/llama-3.1-405b-instruct": ModelPricing(0.005, 0.005, "nvidia"),
    
    # Ollama (local, free)
    "llama3.2": ModelPricing(0.0, 0.0, "ollama"),
    "llama3.1": ModelPricing(0.0, 0.0, "ollama"),
    "codellama": ModelPricing(0.0, 0.0, "ollama"),
    "mistral": ModelPricing(0.0, 0.0, "ollama"),
    "deepseek-coder": ModelPricing(0.0, 0.0, "ollama"),
}

# Default model if unknown
DEFAULT_PRICING = ModelPricing(0.001, 0.002, "unknown")


def get_model_pricing(model: str) -> ModelPricing:
    """
    Get pricing for a model.
    
    Args:
        model: Model name or identifier
        
    Returns:
        ModelPricing object (default if model not found)
    """
    # Check exact match
    if model in MODEL_PRICING:
        return MODEL_PRICING[model]
    
    # Check partial match (e.g., "gpt-4" matches "gpt-4-0613")
    for key, pricing in MODEL_PRICING.items():
        if key in model or model in key:
            return pricing
    
    return DEFAULT_PRICING


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Estimate cost for a request.
    
    Args:
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Estimated cost in USD
    """
    pricing = get_model_pricing(model)
    return pricing.calculate_cost(input_tokens, output_tokens)


def is_free_model(model: str) -> bool:
    """Check if a model is free (Ollama local models)."""
    pricing = get_model_pricing(model)
    return pricing.input_cost_per_1k == 0 and pricing.output_cost_per_1k == 0
