import asyncio
from uuid import uuid4
from .schemas import AskResponse, JobStatus


class Worker:
    def __init__(self, store, graph): self.store, self.graph, self.task = store, graph, None
    def start(self): self.task = asyncio.create_task(self.run())
    async def stop(self):
        if self.task: self.task.cancel(); await asyncio.gather(self.task, return_exceptions=True)
    async def run(self):
        while True:
            job_id = await self.store.dequeue()
            if not job_id: continue
            job = await self.store.get(job_id)
            if not job: continue
            await self.store.update(job_id, status=JobStatus.running)
            try:
                state = await self.graph.ainvoke({"question": job.request.question, "messages": [], "trace": []}, {"configurable": {"thread_id": job.request.thread_id}})
                await self.store.update(job_id, status=JobStatus.completed, result=AskResponse(answer=state["answer"], citations=state.get("citations", []), route=state.get("route", []), trace_id=str(uuid4()), trace=state.get("trace", [])))
            except Exception as exc:
                await self.store.update(job_id, status=JobStatus.failed, error=str(exc))
