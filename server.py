import asyncio
import os
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from agent_A import AgentA, TaskRecord
from agent_B import run_ui_task


class TaskRequest(BaseModel):
    prompt: str
    user_id: str | None = None


app = FastAPI(title="BrowserUse Agents", version="0.1.0")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

agent_a = AgentA()
tasks: Dict[str, TaskRecord] = {}
MAX_CONCURRENT_RUNS = max(int(os.getenv("MAX_CONCURRENT_RUNS", "2")), 1)
task_semaphore = asyncio.Semaphore(MAX_CONCURRENT_RUNS)


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/control", response_class=HTMLResponse)
async def control_room(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/tasks")
async def list_tasks():
    return [task.to_dict() for task in tasks.values()]


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@app.post("/api/tasks", status_code=201)
async def create_task(request: TaskRequest):
    try:
        record = agent_a.create_task(request.prompt, user_id=request.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    tasks[record.id] = record
    loop = asyncio.get_event_loop()
    loop.create_task(_execute_task(record.id))
    return record.to_dict()

@app.get("/api/metrics")
async def metrics():
    return _calculate_metrics()


async def _execute_task(task_id: str):
    record = tasks[task_id]
    async with task_semaphore:
        record.mark_running()
        try:
            result = await run_ui_task(record.prompt)
            record.mark_completed(export_path=result["export_path"], plan=result["plan"])
        except Exception as exc:
            record.mark_failed(str(exc))


def _calculate_metrics():
    total = len(tasks)
    completed = [task for task in tasks.values() if task.status == "completed"]
    durations = [task.duration_seconds for task in completed if task.duration_seconds is not None]
    avg_runtime = None
    if durations:
        avg_runtime = sum(durations) / len(durations)

    latest_task: Optional[TaskRecord] = None
    if completed:
        latest_task = max(
            (task for task in completed if task.finished_at),
            key=lambda task: task.finished_at,
            default=None,
        )

    running = sum(1 for task in tasks.values() if task.status == "running")
    queued = sum(1 for task in tasks.values() if task.status == "queued")
    failed = sum(1 for task in tasks.values() if task.status == "failed")

    return {
        "total_tasks": total,
        "success_count": len(completed),
        "running_count": running,
        "queued_count": queued,
        "failed_count": failed,
        "avg_runtime_seconds": avg_runtime,
        "latest_export_path": latest_task.export_path if latest_task else None,
        "latest_export_finished_at": latest_task.finished_at if latest_task else None,
        "max_concurrent_runs": MAX_CONCURRENT_RUNS,
    }
