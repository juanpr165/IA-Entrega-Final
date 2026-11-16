import re
from langsmith import traceable
from typing import Annotated, Any, Literal, TypedDict
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from .config import get_settings
from .observability import event
from .rag import retrieve
from .schemas import Citation, RouteDecision, ToolInput
from .tools import calculate

Route = Literal["rag", "analyst", "final"]



class IntelligenceState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    question: str
    citations: list[dict[str, Any]]
    rag_completed: bool
    analysis: str
    route: list[dict[str, str]]
    next_agent: Route
    steps: int
    answer: str
    trace: list[dict[str, Any]]


def needs_math(question: str) -> bool:
    return bool(re.search(r"\d\s*[+*/%^]|calcul|porcentaje|promedio", question.casefold()))

@traceable(name="supervisor", run_type="chain")
async def supervisor(state: IntelligenceState) -> dict[str, Any]:
    settings = get_settings()
    q = state["question"]
    if state.get("steps", 0) >= settings.max_graph_steps:
        next_agent, why = "final", "límite de pasos alcanzado"
    elif not state.get("rag_completed", False):
        next_agent, why = "rag", "falta recuperar evidencia del conocimiento"
    elif needs_math(q) and not state.get("analysis"):
        next_agent, why = "analyst", "la solicitud requiere análisis aritmético"
    else:
        next_agent, why = "final", "evidencia suficiente para la síntesis"
    decision = RouteDecision(next_agent=next_agent, rationale=why)
    return {"next_agent": next_agent, "steps": state.get("steps", 0) + 1,
            "route": state.get("route", []) + [decision.model_dump()],
            "trace": state.get("trace", []) + [event("supervisor", why)]}

@traceable(name="rag_agent", run_type="chain")
async def rag_agent(state: IntelligenceState) -> dict[str, Any]:
    citations = await retrieve(state["question"])
    return {
        "citations": [item.model_dump() for item in citations],
        "rag_completed": True,
        "trace": state.get("trace", []) + [event("rag", f"{len(citations)} citas recuperadas")]}


@traceable(name="analyst_agent", run_type="chain")
async def analyst_agent(state: IntelligenceState) -> dict[str, Any]:
    expression = re.search(r"([0-9.() ]+[+*/%^][0-9.() +*/%^]*)", state["question"])
    if expression:
        try:
            result = calculate(ToolInput(expression=expression.group(1).replace("^", "**")))
            text = f"Resultado de la herramienta aritmética: {result.result:g}."
        except (ValueError, SyntaxError, ZeroDivisionError) as exc:
            text = f"No se pudo calcular la expresión: {exc}"
    else:
        text = "No se detectó una expresión aritmética explícita."
    return {"analysis": text, "trace": state.get("trace", []) + [event("analyst", text)]}


def _fallback(state: IntelligenceState) -> str:
    evidence = state.get("citations", [])
    if not evidence:
        return "No encontré evidencia en la base documental local para responder con seguridad."
    lines = ["Respuesta basada en la documentación recuperada:"]
    lines.extend(f"- {item['excerpt']} ({item['source']})" for item in evidence)
    if state.get("analysis"):
        lines.append(state["analysis"])
    return "\n".join(lines)


@traceable(name="final_agent", run_type="chain")
async def final_agent(state: IntelligenceState) -> dict[str, Any]:
    settings = get_settings()
    answer = _fallback(state)
    # Groq is always async and optional: tests/local demo remain useful without a key.
    if settings.groq_api_key:
        llm = ChatGroq(model=settings.groq_model, api_key=settings.groq_api_key, temperature=0)
        evidence = "\n".join(f"[{x['source']}] {x['excerpt']}" for x in state.get("citations", []))
        response = await llm.ainvoke([SystemMessage(content="Respondé en español usando sólo la evidencia provista."),
            HumanMessage(content=f"Pregunta: {state['question']}\nEvidencia:\n{evidence}\n{state.get('analysis', '')}")])
        answer = str(response.content)
    return {"answer": answer, "trace": state.get("trace", []) + [event("final", "síntesis completada")]} 


def build_graph(checkpointer: Any):
    graph = StateGraph(IntelligenceState)
    graph.add_node("supervisor", supervisor)
    graph.add_node("rag", rag_agent)
    graph.add_node("analyst", analyst_agent)
    graph.add_node("final", final_agent)
    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges("supervisor", lambda state: state["next_agent"], {"rag": "rag", "analyst": "analyst", "final": "final"})
    graph.add_edge("rag", "supervisor")
    graph.add_edge("analyst", "supervisor")
    graph.add_edge("final", END)
    return graph.compile(checkpointer=checkpointer)
