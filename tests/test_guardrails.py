import pytest
from pydantic import BaseModel

from llm_observability.guardrails import validate_output, GuardrailValidationError


class CategoryResult(BaseModel):
    category: str


def test_valid_dict_passes():
    result = validate_output({"category": "Food"}, CategoryResult)
    assert result.category == "Food"


def test_invalid_shape_raises():
    with pytest.raises(GuardrailValidationError):
        validate_output({"wrong_field": "x"}, CategoryResult)
