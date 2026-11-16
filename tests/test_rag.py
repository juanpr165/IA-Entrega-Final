import pytest
from app.rag import retrieve


@pytest.mark.asyncio
async def test_rag_returns_citation_for_library_hours(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    folder = tmp_path / "knowledge"; folder.mkdir()
    (folder / "reglas.md").write_text("La biblioteca abre de lunes a viernes a las 9 horas.", encoding="utf-8")
    citations = await retrieve("¿Qué horario tiene la biblioteca?")
    assert citations and citations[0].source == "reglas.md"
