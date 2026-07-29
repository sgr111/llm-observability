# llm-observability

A small, shared Python package that adds **logging, prompt versioning,
evaluation, and output guardrails** to LLM calls — meant to be imported into
multiple projects rather than run as its own service.

Built to close a specific gap: [Activity Tracker](https://github.com/sgr111/activity-tracker-api)
(Gemini) and [Bill Splitter](https://github.com/sgr111/bill-splitter) (Groq +
LangChain/LangGraph) both make real LLM calls with no shared way to log them,
version their prompts, or catch regressions when a prompt changes. This
package is that shared layer — plug it into any project that makes an LLM
call, including the planned AI Chief of Staff orchestrator.

## What this is *not*

- Not a deployed service — no API endpoints, no server, nothing to host.
- Not a database of its own — it writes to a `llm_calls` table that lives in
  *your* project's existing Postgres DB (see `migrations/`).
- Not a prompt-engineering tool — it manages and versions the prompts you
  write; it doesn't write them for you.

## What it covers

| Piece | File | What it does |
|---|---|---|
| Logging | `logger.py` | Wraps any async LLM call, logs prompt/response/latency/success to DB (or console if no DB is wired yet) |
| Prompt versioning | `prompts/registry.py` | Named, versioned prompt templates loaded from a YAML file instead of inline strings |
| Eval harness | `eval/harness.py` | Replays a fixed set of test cases against a prompt/function, computes a pass rate, flags regressions |
| Guardrails | `guardrails.py` | Validates LLM output against a Pydantic schema, with an optional retry-once decorator |

## Install into a host project

Until this is pushed to PyPI, install directly from the local path or a
GitHub URL:

```bash
# from a local clone
pip install -e ../llm-observability

# or once pushed to GitHub
pip install git+https://github.com/sgr111/llm-observability.git
```

Then add the `llm_calls` table to your project's own DB — adapt
`migrations/001_create_llm_calls_table.sql` into an Alembic migration.

## Quick usage

```python
from llm_observability import track_llm_call, PromptRegistry

registry = PromptRegistry.from_yaml("prompts.yaml")

async def ask_gemini(prompt: str) -> str:
    # your real Gemini/Groq call here
    ...

async def ask(question: str, context: str, db_session):
    template = registry.get("rag_answer")  # active version by default
    final_prompt = template.render(question=question, context=context)

    return await track_llm_call(
        fn=ask_gemini,
        args=(final_prompt,),
        project="activity-tracker",
        feature="rag_qa",
        provider="gemini",
        prompt_name=template.name,
        prompt_version=template.version,
        db_session=db_session,
    )
```

See `examples/usage_example.py` and `examples/prompts.example.yaml` for a
fuller worked example.

## Status

This is v0.1 — a working skeleton, not a finished library. Current TODOs
(see inline `# TODO` comments in the code):

- [ ] Real token counting + cost estimation per provider (Gemini vs Groq pricing)
- [ ] Smarter prompt-text extraction in `logger.py` (currently a best-effort guess)
- [ ] Redaction rules before logging prompt/response text (PII safety)
- [ ] First real integration: wire into Activity Tracker's `ai_service.py`
- [ ] Second integration: wire into Bill Splitter's `langchain_qa.py` / `langgraph_agent.py`
- [ ] Optional later upgrade: swap the manual logger for LangSmith once
      LangChain is used consistently across projects

## Project structure

```
llm-observability/
├── llm_observability/
│   ├── __init__.py          # public API surface
│   ├── config.py            # package-level settings (pydantic-settings)
│   ├── models.py            # LLMCallLog SQLAlchemy model
│   ├── logger.py            # track_llm_call() — the main wrapper
│   ├── guardrails.py        # validate_output(), with_retry_on_invalid()
│   ├── prompts/
│   │   └── registry.py      # PromptRegistry, PromptTemplate
│   └── eval/
│       └── harness.py       # EvalCase, run_eval()
├── migrations/
│   └── 001_create_llm_calls_table.sql
├── examples/
│   ├── usage_example.py
│   └── prompts.example.yaml
├── tests/
├── pyproject.toml
├── requirements.txt
└── .env.example
```

## Author

**Sourabh Sagar** — Backend Developer & QA Automation Engineer
Lucknow, Uttar Pradesh, India · [github.com/sgr111](https://github.com/sgr111) · sgrsourabh111@gmail.com
