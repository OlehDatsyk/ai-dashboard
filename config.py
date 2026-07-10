"""
config.py
=========
Centralized application configuration.

Loads environment variables from a `.env` file (via python-dotenv) and
exposes a single `Config` object used throughout the application. Keeping
configuration in one place makes the rest of the codebase environment
agnostic and easy to test.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load variables from .env into the process environment as early as possible.
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _bool_env(name: str, default: bool = False) -> bool:
    """Parse a boolean-ish environment variable ('True', '1', 'yes', ...)."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class ModelPricing:
    """Approximate per-1K-token USD pricing used for cost estimation.

    These are illustrative defaults and should be updated to match your
    current OpenAI pricing plan. Prices are expressed in USD per 1,000
    tokens for prompt (input) and completion (output) tokens respectively.
    """

    prompt_per_1k: float
    completion_per_1k: float


# Static pricing table. Extend this as new models are added.
MODEL_PRICING: dict[str, ModelPricing] = {
    "gpt-4o": ModelPricing(prompt_per_1k=0.005, completion_per_1k=0.015),
    "gpt-4o-mini": ModelPricing(prompt_per_1k=0.00015, completion_per_1k=0.0006),
    "gpt-4.1": ModelPricing(prompt_per_1k=0.002, completion_per_1k=0.008),
    "gpt-4.1-mini": ModelPricing(prompt_per_1k=0.0004, completion_per_1k=0.0016),
    "gpt-4.1-nano": ModelPricing(prompt_per_1k=0.0001, completion_per_1k=0.0004),
    "o3-mini": ModelPricing(prompt_per_1k=0.0011, completion_per_1k=0.0044),
}

AVAILABLE_MODELS = list(MODEL_PRICING.keys())

DEFAULT_PRICING = ModelPricing(prompt_per_1k=0.0005, completion_per_1k=0.0015)


@dataclass(frozen=True)
class Config:
    """Application-wide configuration object."""

    # --- OpenAI ---
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    default_model: str = field(default_factory=lambda: os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini"))
    default_temperature: float = field(default_factory=lambda: _float_env("OPENAI_DEFAULT_TEMPERATURE", 0.7))
    default_system_prompt: str = field(
        default_factory=lambda: os.getenv(
            "OPENAI_SYSTEM_PROMPT",
            "You are a helpful, concise AI assistant embedded inside an analytics dashboard.",
        )
    )

    # --- Flask ---
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", "dev-secret-key"))
    debug: bool = field(default_factory=lambda: _bool_env("FLASK_DEBUG", True))
    host: str = field(default_factory=lambda: os.getenv("HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "5000")))

    # --- Application ---
    data_dir: Path = field(default_factory=lambda: BASE_DIR / os.getenv("DATA_DIR", "data"))
    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "AI Dashboard"))
    currency_symbol: str = field(default_factory=lambda: os.getenv("CURRENCY_SYMBOL", "$"))

    def validate(self) -> list[str]:
        """Return a list of human readable configuration warnings (non-fatal)."""
        warnings: list[str] = []
        if not self.openai_api_key or self.openai_api_key.startswith("sk-your"):
            warnings.append(
                "OPENAI_API_KEY is not set. AI features will be disabled until you add a "
                "valid key to your .env file."
            )
        if self.secret_key == "dev-secret-key":
            warnings.append("Using the default SECRET_KEY. Set a unique SECRET_KEY before deploying.")
        return warnings


config = Config()
config.data_dir.mkdir(parents=True, exist_ok=True)
