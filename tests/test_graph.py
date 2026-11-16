import pytest
from app.graph import analyst_agent, supervisor


@pytest.mark.asyncio
async def test_supervisor_routes_first_to_rag():
    result = await supervisor({"question": "¿Qué horario tiene la biblioteca?", "trace": []})
    assert result["next_agent"] == "rag"
    assert result["trace"][0]["node"] == "supervisor"


@pytest.mark.asyncio
async def test_analyst_emits_trace_and_result():
    result = await analyst_agent({"question": "Calculá 2 + 3", "trace": []})
    assert "5" in result["analysis"]
    assert result["trace"][0]["node"] == "analyst"
