# run.py

import asyncio

from agent_A import AgentA
from agent_B import run_ui_task


async def main():
    user_input = input("Describe the task Agent B should perform: ").strip()

    agent_a = AgentA(source="cli")

    try:
        task = agent_a.create_task(user_input, user_id="cli-user")
    except ValueError as exc:
        print(f" Agent A rejected the request: {exc}")
        return

    print(f"\n Task accepted (id: {task.id}). Agent B is planning...\n")

    task.mark_running()

    try:
        result = await run_ui_task(task.prompt)
        task.mark_completed(export_path=result["export_path"], plan=result["plan"])
    except Exception as exc:
        task.mark_failed(str(exc))
        print(f" Agent B failed: {exc}")
        return
    
    print(f" Artifacts: {task.export_path}")


if __name__ == "__main__":
    asyncio.run(main())
