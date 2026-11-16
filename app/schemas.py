from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field


class JobStatus(StrEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class AskRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    question: str = Field(min_length=3, max_length=4000, examples=["¿Cuál es el horario de préstamos?"])
    thread_id: str = Field(min_length=1, max_length=128, pattern=r"^[a-zA-Z0-9_-]+$")


class Citation(BaseModel):
    source: str = Field(min_length=1)
    excerpt: str = Field(min_length=1)
    score: float = Field(ge=0, le=1)


class ToolInput(BaseModel):
    expression: str = Field(min_length=1, max_length=100)


class ToolOutput(BaseModel):
    result: float


class RouteDecision(BaseModel):
    next_agent: str = Field(pattern="^(rag|analyst|final)$")
    rationale: str = Field(min_length=1, max_length=300)


class TraceEvent(BaseModel):
    node: str
    at: datetime
    detail: str


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation] = []
    route: list[RouteDecision] = []
    trace_id: str
    trace: list[TraceEvent] = []


class JobRecord(BaseModel):
    job_id: str
    request: AskRequest
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    result: AskResponse | None = None
    error: str | None = None
