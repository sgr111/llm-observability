import pytest
from llm_observability.eval.harness import EvalCase, run_eval


@pytest.mark.asyncio
async def test_run_eval_computes_pass_rate():
    async def call_fn(question: str) -> str:
        return f"answer to {question}"

    cases = [
        EvalCase(input={"question": "a"}, check=lambda out: "answer" in out),
        EvalCase(input={"question": "b"}, check=lambda out: "nope" in out),  # will fail
    ]

    report = await run_eval(cases, call_fn)
    assert report.pass_rate == 0.5
    assert len(report.results) == 2
