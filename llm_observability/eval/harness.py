"""
A small eval harness: replay a fixed set of test cases against a prompt
version and flag regressions. Meant to slot into the same pytest suites you
already run (e.g. Activity Tracker's real-API integration tests) rather than
being a separate tool to learn.

Usage:

    from llm_observability.eval.harness import EvalCase, run_eval

    cases = [
        EvalCase(
            input={"question": "How many events yesterday?"},
            check=lambda output: "yesterday" in output.lower(),
        ),
        EvalCase(
            input={"question": "asdkjaskjd nonsense"},
            check=lambda output: "don't know" in output.lower() or "cannot" in output.lower(),
        ),
    ]

    report = await run_eval(cases, call_fn=my_rag_qa_function)
    assert report.pass_rate >= 0.9   # fails CI if prompt regresses
"""
from dataclasses import dataclass, field
from typing import Any, Callable, List

from ..config import settings


@dataclass
class EvalCase:
    input: dict                          # kwargs passed to call_fn
    check: Callable[[Any], bool]         # returns True if output is acceptable
    name: str = ""


@dataclass
class EvalResult:
    case_name: str
    passed: bool
    output: Any = None
    error: str = None


@dataclass
class EvalReport:
    results: List[EvalResult] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        if not self.results:
            return 1.0
        return sum(1 for r in self.results if r.passed) / len(self.results)

    @property
    def is_regression(self) -> bool:
        return self.pass_rate < settings.eval_regression_threshold


async def run_eval(cases: List[EvalCase], call_fn: Callable[..., Any]) -> EvalReport:
    report = EvalReport()
    for i, case in enumerate(cases):
        name = case.name or f"case_{i}"
        try:
            output = await call_fn(**case.input)
            passed = bool(case.check(output))
            report.results.append(EvalResult(case_name=name, passed=passed, output=output))
        except Exception as exc:
            report.results.append(EvalResult(case_name=name, passed=False, error=str(exc)))
    return report
