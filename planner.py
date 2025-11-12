# planner.py

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from openai import AsyncOpenAI


PLAN_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["objective", "steps", "success_criteria"],
    "properties": {
        "objective": {"type": "string"},
        "starting_url": {"type": "string", "format": "uri"},
        "notes": {"type": "string"},
        "steps": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["title", "action"],
                "properties": {
                    "title": {"type": "string"},
                    "action": {"type": "string"},
                    "expected_result": {"type": "string"},
                },
                "additionalProperties": False,
            },
        },
        "success_criteria": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string"},
        },
    },
}


class GPTPlanner:
    """Creates structured instructions for BrowserUse using GPT-4o."""

    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.3):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required for planning but is missing.")

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    async def create_plan(self, prompt: str) -> Dict[str, Any]:
        """Call GPT-4o to transform natural language into a deterministic JSON plan."""
        response = await self.client.responses.create(
            model=self.model,
            temperature=self.temperature,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are a task planner for a browser automation agent. "
                        "Stay strictly on the user request, avoid inventing extra goals or sub‑tasks.\n"
                        "Respond ONLY with valid JSON that matches this schema:\n"
                        f"{json.dumps(PLAN_SCHEMA)}\n"
                        "Limit yourself to the essential steps (ideally ≤5). "
                        "If the user does not mention a starting URL, default to https://www.google.com."
                    ),
                },
                {"role": "user", "content": prompt.strip()},
            ],
        )

        try:
            content = response.output[0].content[0].text  # type: ignore[attr-defined]
            text = content.strip()
            if text.startswith("```"):
                text = text.strip("`")
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            plan = json.loads(text)
        except Exception as exc:
            raise RuntimeError(f"Planner response could not be parsed: {exc}") from exc

        if "starting_url" not in plan or not plan["starting_url"]:
            plan["starting_url"] = "https://www.google.com"
        return plan


def render_plan_for_agent(prompt: str, plan: Dict[str, Any]) -> str:
    """Format plan dict into human-readable instructions for BrowserUse."""
    steps: List[Dict[str, str]] = plan.get("steps", [])
    success = plan.get("success_criteria", [])
    notes = plan.get("notes")

    lines = [
        f"User request: {prompt}",
        "",
        f"Objective: {plan.get('objective', 'Follow the user request carefully.')}",
        "",
        "Follow these steps sequentially:",
    ]
    for index, step in enumerate(steps, start=1):
        lines.append(f"{index}. {step.get('title', 'Step')}: {step.get('action', '').strip()}")
        if step.get("expected_result"):
            lines.append(f"   Expected result: {step['expected_result'].strip()}")

    if notes:
        lines.append("")
        lines.append(f"Notes: {notes.strip()}")

    if success:
        lines.append("")
        lines.append("Confirm success when all of the following are satisfied:")
        for item in success:
            lines.append(f"- {item}")

    lines.append("")
    lines.append("When the success criteria are met, finish with the done action.")
    return "\n".join(lines)
