# agent_B.py

from __future__ import annotations

import json
import os
import shutil
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from browser_use import Agent, Browser, ChatBrowserUse

from planner import GPTPlanner, render_plan_for_agent

load_dotenv()

EXPORT_DIR = "exports"
DEFAULT_MAX_STEPS = 20

_planner: Optional[GPTPlanner] = None


def _get_planner() -> GPTPlanner:
    global _planner
    if _planner is None:
        _planner = GPTPlanner()
    return _planner


def _save_history_artifacts(history, export_path: str, plan: Dict[str, Any], prompt: str):
    """
    Persist the agent run artifacts (trace + screenshots) into the export folder.
    """
    trace_file = os.path.join(export_path, "trace.json")
    history.save_to_file(trace_file)

    plan_file = os.path.join(export_path, "plan.json")
    run_meta_file = os.path.join(export_path, "run.json")

    with open(plan_file, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)

    with open(run_meta_file, "w", encoding="utf-8") as f:
        json.dump({"prompt": prompt}, f, indent=2)

    screenshot_paths: List[Optional[str]] = history.screenshot_paths()
    for idx, screenshot_path in enumerate(screenshot_paths):
        if not screenshot_path or not os.path.exists(screenshot_path):
            continue
        destination = os.path.join(export_path, f"step_{idx}.png")
        shutil.copy2(screenshot_path, destination)


def _build_browser() -> Browser:
    """
    Build a Browser instance that reuses a local Chrome profile when env vars are set.
    Falls back to default BrowserUse Chromium when not configured.
    """
    def _clean(value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        cleaned = value.strip().strip('"').strip("'")
        return os.path.expanduser(os.path.expandvars(cleaned))

    executable = _clean(os.getenv("CHROME_EXECUTABLE"))
    user_data_dir = _clean(os.getenv("CHROME_USER_DATA_DIR"))
    profile_directory = _clean(os.getenv("CHROME_PROFILE_DIRECTORY"))
    headless_value = os.getenv("BROWSER_HEADLESS")
    extra_args = os.getenv("BROWSER_EXTRA_ARGS")

    browser_kwargs: Dict[str, Any] = {}
    if executable:
        browser_kwargs["executable_path"] = executable
    if user_data_dir:
        browser_kwargs["user_data_dir"] = user_data_dir
    if profile_directory:
        browser_kwargs["profile_directory"] = profile_directory
    if headless_value is not None:
        browser_kwargs["headless"] = headless_value.lower() == "true"
    if extra_args:
        extra_args_list = [arg for arg in extra_args.split() if arg]
        if extra_args_list:
            browser_kwargs["args"] = extra_args_list

    if not browser_kwargs:
        return Browser()

    return Browser(**browser_kwargs)


async def run_ui_task(task_prompt: str):
    # Create output directory
    timestamp = datetime.now().strftime("run_%Y%m%d_%H%M")
    path = os.path.join(EXPORT_DIR, timestamp)
    os.makedirs(path, exist_ok=True)

    print(f"\n🧠 Agent B executing:\nPrompt: {task_prompt}\n")

    planner = _get_planner()
    plan = await planner.create_plan(task_prompt)
    instructions = render_plan_for_agent(task_prompt, plan)
    starting_url = plan.get("starting_url", "https://www.google.com")

    initial_actions = [
        {
            "navigate": {
                "url": starting_url,
                "new_tab": False,
            }
        }
    ]

    # Create LLM
    llm = ChatBrowserUse(api_key=os.getenv("BROWSER_USE_API_KEY"))

    # Create the agent
    agent = Agent(
        task=instructions,
        llm=llm,
        browser=_build_browser(),
        use_vision=True,
        generate_gif=os.path.join(path, "agent_history.gif"),   # optional
        initial_actions=initial_actions,
    )

    # Run the agent
    history = await agent.run(max_steps=DEFAULT_MAX_STEPS)

    # Save results
    _save_history_artifacts(history, path, plan, task_prompt)

    print(f"📸 Task completed. Trace saved in: {path}")
    return {"export_path": path, "plan": plan}
