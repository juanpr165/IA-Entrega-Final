import pytest
from app.schemas import ToolInput
from app.tools import calculate


def test_calculator_uses_validated_expression():
    assert calculate(ToolInput(expression="(2 + 3) * 4")).result == 20


def test_calculator_rejects_python_code():
    with pytest.raises(ValueError):
        calculate(ToolInput(expression="__import__('os').system('x')"))
