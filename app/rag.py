import unicodedata
from pathlib import Path

from .schemas import Citation


def normalizar(texto: str) -> str:
    return "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto.casefold())
        if unicodedata.category(caracter) != "Mn"
    )


async def retrieve(question: str, limit: int = 3) -> list[Citation]:
    """RAG léxico local, tolerante a tildes."""
    terminos = {
        normalizar(palabra).strip("¿?.,:;")
        for palabra in question.split()
        if len(palabra) > 2
    }

    hits: list[Citation] = []

    for path in Path("knowledge").glob("*.md"):
        text = path.read_text(encoding="utf-8")

        lineas = [
            line
            for line in text.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]

        texto_normalizado = normalizar("\n".join(lineas))
        matched = sum(
            termino in texto_normalizado
            for termino in terminos
        )

        if matched:
            excerpt = max(
            lineas,
            key=lambda line: sum(
                termino in normalizar(line)
                for termino in terminos
            ),
            default=text[:240],
        )

            hits.append(
            Citation(
                source=path.name,
                excerpt=excerpt[:500],
                score=round(matched / max(len(terminos), 1), 2),
            )
        )

    return sorted(hits, key=lambda item: item.score, reverse=True)[:limit]