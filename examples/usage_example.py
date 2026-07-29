"""
Worked example: how Activity Tracker's RAG Q&A would use this package.
Not runnable as-is (gemini_client/db are stand-ins) — shows the wiring pattern.
"""
import asyncio

from llm_observability import track_llm_call, PromptRegistry, run_eval, EvalCase

registry = PromptRegistry.from_yaml("prompts.yaml")


async def gemini_rag_answer(question: str, context: str) -> str:
    template = registry.get("rag_answer")  # uses whichever version is marked active
    final_prompt = template.render(question=question, context=context)

    # response = await gemini_client.generate(final_prompt)   # real call
    response_text = "stubbed response"  # placeholder for this example
    return response_text


async def ask(question: str, context: str, db_session=None) -> str:
    template = registry.get("rag_answer")
    return await track_llm_call(
        fn=gemini_rag_answer,
        kwargs={"question": question, "context": context},
        project="activity-tracker",
        feature="rag_qa",
        provider="gemini",
        model="gemini-1.5-flash",
        prompt_name=template.name,
        prompt_version=template.version,
        db_session=db_session,  # pass your real AsyncSession here
    )


async def eval_rag_prompt():
    cases = [
        EvalCase(
            input={"question": "What did I log yesterday?", "context": "..."},
            check=lambda out: len(out) > 0,
        ),
    ]
    report = await run_eval(cases, call_fn=lambda **kw: gemini_rag_answer(**kw))
    print(f"pass_rate={report.pass_rate}, regression={report.is_regression}")


if __name__ == "__main__":
    asyncio.run(ask("What did I log yesterday?", context="some events..."))
    asyncio.run(eval_rag_prompt())
