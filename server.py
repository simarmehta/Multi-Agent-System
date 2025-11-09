import asyncio
from typing import Dict

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


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
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


async def _execute_task(task_id: str):
    record = tasks[task_id]
    record.mark_running()
    try:
        result = await run_ui_task(record.prompt)
        record.mark_completed(export_path=result["export_path"], plan=result["plan"])
    except Exception as exc:
        record.mark_failed(str(exc))
