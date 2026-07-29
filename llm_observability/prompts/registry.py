"""
Prompt versioning registry.

Goal: prompts live as versioned, named templates instead of inline strings
scattered across the codebase — so a prompt change is visible in a diff,
traceable in llm_calls.prompt_version, and revertible.

Usage:

    from llm_observability.prompts.registry import PromptRegistry

    registry = PromptRegistry.from_yaml("prompts.yaml")
    template = registry.get("rag_answer", version="v2")
    final_prompt = template.render(question="...", context="...")

prompts.yaml (per host project, lives in that project's own repo) looks like:

    rag_answer:
      v1:
        template: "Answer using only this context: {context}\\n\\nQ: {question}"
      v2:
        template: "You are a helpful assistant. Context:\\n{context}\\n\\nQuestion: {question}\\nAnswer strictly from context; say 'I don't know' if not covered."
        active: true   # marks this as the current default version
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import yaml


@dataclass
class PromptTemplate:
    name: str
    version: str
    template: str

    def render(self, **kwargs) -> str:
        return self.template.format(**kwargs)


class PromptRegistry:
    def __init__(self, data: Dict[str, Dict[str, dict]]):
        # data shape: { prompt_name: { version: {template, active?} } }
        self._data = data

    @classmethod
    def from_yaml(cls, path: str) -> "PromptRegistry":
        raw = yaml.safe_load(Path(path).read_text())
        return cls(raw or {})

    def get(self, name: str, version: Optional[str] = None) -> PromptTemplate:
        versions = self._data.get(name)
        if not versions:
            raise KeyError(f"No prompt registered under name '{name}'")

        if version is None:
            # fall back to whichever version is marked active, else the latest key
            version = next(
                (v for v, cfg in versions.items() if cfg.get("active")),
                sorted(versions.keys())[-1],
            )

        cfg = versions.get(version)
        if not cfg:
            raise KeyError(f"Prompt '{name}' has no version '{version}'")

        return PromptTemplate(name=name, version=version, template=cfg["template"])

    def list_versions(self, name: str) -> list:
        return list(self._data.get(name, {}).keys())
