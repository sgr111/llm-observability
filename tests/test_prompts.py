import pytest
from llm_observability.prompts.registry import PromptRegistry


@pytest.fixture
def registry(tmp_path):
    yaml_content = """
rag_answer:
  v1:
    template: "Q: {question}"
  v2:
    template: "Question: {question}"
    active: true
"""
    p = tmp_path / "prompts.yaml"
    p.write_text(yaml_content)
    return PromptRegistry.from_yaml(str(p))


def test_get_active_version(registry):
    template = registry.get("rag_answer")
    assert template.version == "v2"
    assert template.render(question="hi") == "Question: hi"


def test_get_specific_version(registry):
    template = registry.get("rag_answer", version="v1")
    assert template.render(question="hi") == "Q: hi"


def test_missing_prompt_raises(registry):
    with pytest.raises(KeyError):
        registry.get("does_not_exist")
