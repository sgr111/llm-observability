import pytest
from llm_observability.logger import track_llm_call


@pytest.mark.asyncio
async def test_track_llm_call_returns_fn_result_without_db():
    async def fake_llm(prompt: str) -> str:
        return f"echo: {prompt}"

    result = await track_llm_call(
        fn=fake_llm,
        args=("hello",),
        project="test-project",
        feature="test-feature",
        provider="fake",
        db_session=None,  # console fallback path
    )
    assert result == "echo: hello"


@pytest.mark.asyncio
async def test_track_llm_call_propagates_exceptions():
    async def failing_llm(prompt: str) -> str:
        raise ValueError("provider error")

    with pytest.raises(ValueError):
        await track_llm_call(
            fn=failing_llm,
            args=("hello",),
            project="test-project",
            feature="test-feature",
            provider="fake",
            db_session=None,
        )
