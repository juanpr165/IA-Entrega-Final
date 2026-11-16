import json
from datetime import UTC, datetime
from redis.asyncio import Redis
from .schemas import JobRecord, JobStatus


class JobStore:
    def __init__(self, redis: Redis, queue_key: str): self.redis, self.queue_key = redis, queue_key
    def key(self, job_id: str) -> str: return f"ia-final:job:{job_id}"
    async def create(self, record: JobRecord) -> None: await self.redis.set(self.key(record.job_id), record.model_dump_json())
    async def get(self, job_id: str) -> JobRecord | None:
        raw = await self.redis.get(self.key(job_id)); return JobRecord.model_validate_json(raw) if raw else None
    async def update(self, job_id: str, **changes: object) -> JobRecord:
        old = await self.get(job_id)
        if old is None: raise KeyError(job_id)
        new = old.model_copy(update={**changes, "updated_at": datetime.now(UTC)})
        await self.create(new); return new
    async def enqueue(self, job_id: str) -> None: await self.redis.rpush(self.queue_key, json.dumps({"job_id": job_id}))
    async def dequeue(self) -> str | None:
        item = await self.redis.blpop(self.queue_key, timeout=1); return json.loads(item[1])["job_id"] if item else None
