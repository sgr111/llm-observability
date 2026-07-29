"""
Guardrails: a thin validation layer on LLM output before it reaches the user.

Two building blocks:
1. validate_output()  — check a raw LLM response against a Pydantic schema
                         (for structured outputs, e.g. categorization results)
2. with_retry_on_invalid() — decorator that retries a call once if the output
                         fails validation, then raises rather than silently
                         returning bad data

Usage:

    from pydantic import BaseModel
    from llm_observability.guardrails import validate_output

    class CategoryResult(BaseModel):
        category: str

    raw = await ask_groq_to_categorize(expense_desc)
    result = validate_output(raw, CategoryResult)  # raises if malformed/empty
"""
import functools
import logging
from typing import Any, Callable, Type, TypeVar

from pydantic import BaseModel, ValidationError

from .config import settings

logger = logging.getLogger("llm_observability")

T = TypeVar("T", bound=BaseModel)


class GuardrailValidationError(Exception):
    """Raised when an LLM response fails guardrail checks after retries."""


def validate_output(raw: Any, schema: Type[T]) -> T:
    """
    Validates raw LLM output (dict or JSON string) against a Pydantic schema.
    Also rejects trivially-empty responses even for free-text (non-schema) cases
    by checking schema constraints — add stricter empty/refusal checks here as
    each project's failure modes become clear (e.g. "I cannot help with that").
    """
    try:
        if isinstance(raw, (dict,)):
            return schema.model_validate(raw)
        return schema.model_validate_json(raw)
    except ValidationError as exc:
        raise GuardrailValidationError(f"LLM output failed schema validation: {exc}") from exc


def with_retry_on_invalid(schema: Type[BaseModel]):
    """
    Decorator: calls the wrapped async function, validates its output against
    `schema`, and retries once (per settings.max_retry_on_invalid_output) before
    raising GuardrailValidationError.
    """
    def decorator(fn: Callable):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            attempts = settings.max_retry_on_invalid_output + 1
            last_error = None
            for attempt in range(attempts):
                raw = await fn(*args, **kwargs)
                try:
                    return validate_output(raw, schema)
                except GuardrailValidationError as exc:
                    last_error = exc
                    logger.warning(
                        "guardrail retry %s/%s for %s", attempt + 1, attempts, fn.__name__
                    )
            raise last_error
        return wrapper
    return decorator
