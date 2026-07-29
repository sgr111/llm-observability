"""
Central settings for the llm_observability package.

Each host project (Activity Tracker, Bill Splitter, AI Chief of Staff) passes
its own DB connection when initializing the logger — this file only holds
package-level toggles that stay the same regardless of which project imports it.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class ObservabilitySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LLMOBS_", env_file=".env", extra="ignore")

    # Master switch — if False, log_llm_call() becomes a no-op (useful in tests)
    enabled: bool = True

    # If a DB session isn't passed explicitly, fall back to console/JSON logging
    # instead of failing — observability should never break the calling app.
    fail_open: bool = True

    # Guardrails
    max_retry_on_invalid_output: int = 1

    # Eval harness
    eval_regression_threshold: float = 0.9  # min pass-rate before flagging a regression


settings = ObservabilitySettings()
