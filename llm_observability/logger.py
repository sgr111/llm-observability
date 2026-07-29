"""
Core logging wrapper.

Usage (in any host project):

    from llm_observability import track_llm_call

    async def ask_gemini(prompt: str) -> str:
        response = await gemini_client.generate(prompt)
        return response.text

    result = await track_llm_call(
        fn=ask_gemini,
        args=(prompt,),
        project="activity-tracker",
        feature="rag_qa",
        provider="gemini",
        model="gemini-1.5-flash",
        prompt_name="rag_answer",
        prompt_version="v2",
        db_session=db,   # any AsyncSession — pass None to log to console instead
    )

This is a SKELETON: token counting, cost estimation, and console-mode logging
are stubbed with TODOs — fill in per-provider details when wiring this into
each project.
"""
import time
import logging
from typing import Any, Awaitable, Callable, Optional

from .config import settings
from .models import LLMCallLog

logger = logging.getLogger("llm_observability")


async def track_llm_call(
    fn: Callable[..., Awaitable[Any]],
    args: tuple = (),
    kwargs: Optional[dict] = None,
    *,
    project: str,
    feature: str,
    provider: str,
    model: Optional[str] = None,
    prompt_name: Optional[str] = None,
    prompt_version: Optional[str] = None,
    db_session=None,  # AsyncSession from the host project, or None
) -> Any:
    """
    Wraps a single LLM call, measures latency, and logs the result.
    Returns whatever `fn` returns — failures in logging never break the caller
    (fail_open), but failures in `fn` itself still propagate normally.
    """
    kwargs = kwargs or {}

    if not settings.enabled:
        return await fn(*args, **kwargs)

    prompt_text = _extract_prompt_for_logging(args, kwargs)
    start = time.monotonic()
    success = True
    error_message = None
    response_text = None

    try:
        result = await fn(*args, **kwargs)
        response_text = str(result)[:4000]  # TODO: cap/redact per project's needs
        return result
    except Exception as exc:
        success = False
        error_message = str(exc)
        raise
    finally:
        latency_ms = int((time.monotonic() - start) * 1000)
        await _persist_log(
            db_session=db_session,
            project=project,
            feature=feature,
            provider=provider,
            model=model,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            prompt_text=prompt_text,
            response_text=response_text,
            latency_ms=latency_ms,
            success=success,
            error_message=error_message,
        )


def _extract_prompt_for_logging(args: tuple, kwargs: dict) -> Optional[str]:
    # TODO: make this smarter per call-site — for now, best-effort guess.
    if args:
        return str(args[0])[:4000]
    if "prompt" in kwargs:
        return str(kwargs["prompt"])[:4000]
    return None


async def _persist_log(*, db_session, **fields) -> None:
    log_row = LLMCallLog(**fields)

    if db_session is None:
        # Console/JSON fallback — no DB wired up yet for this project.
        logger.info("llm_call", extra={"log": fields})
        return

    try:
        db_session.add(log_row)
        await db_session.commit()
    except Exception:
        if settings.fail_open:
            logger.exception("llm_observability: failed to persist log, continuing")
        else:
            raise
