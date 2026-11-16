import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from fastapi import FastAPI, HTTPException, Request, status
from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from redis.asyncio import Redis
from .config import get_settings
from .graph import build_graph
from .schemas import AskRequest, JobRecord, JobStatus
from .store import JobStore
from .worker import Worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings(); redis = Redis.from_url(settings.redis_url, decode_responses=True); await redis.ping()
    context = AsyncRedisSaver.from_conn_string(settings.redis_url); saver = await context.__aenter__(); await saver.asetup()
    app.state.store = JobStore(redis, settings.queue_key); app.state.worker = Worker(app.state.store, build_graph(saver)); app.state.worker.start()
    try: yield
    finally: await app.state.worker.stop(); await context.__aexit__(None, None, None); await redis.aclose()


app = FastAPI(title="IA Entrega Final", version="1.0.0", lifespan=lifespan)

@app.get("/health")
async def health(request: Request) -> dict[str, str]:
    await request.app.state.store.redis.ping(); return {"status": "ok"}

@app.post("/tasks", response_model=JobRecord, status_code=status.HTTP_202_ACCEPTED)
async def create_task(payload: AskRequest, request: Request) -> JobRecord:
    now = datetime.now(UTC); job = JobRecord(job_id=str(uuid.uuid4()), request=payload, status=JobStatus.pending, created_at=now, updated_at=now)
    await request.app.state.store.create(job); await request.app.state.store.enqueue(job.job_id); return job

@app.get("/tasks/{job_id}", response_model=JobRecord)
async def task(job_id: str, request: Request) -> JobRecord:
    result = await request.app.state.store.get(job_id)
    if result is None: raise HTTPException(404, "Tarea inexistente")
    return result
