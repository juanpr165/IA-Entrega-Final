import pytest
from pydantic import ValidationError
from app.schemas import AskRequest


def test_request_rejects_invalid_thread_id():
    with pytest.raises(ValidationError):
        AskRequest(question="consulta válida", thread_id="con espacios")


def test_request_accepts_valid_payload():
    payload = AskRequest(question="¿Cuál es el horario?", thread_id="demo_01")
    assert payload.thread_id == "demo_01"
