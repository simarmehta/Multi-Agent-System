import os
import json

def trace_to_markdown(folder):
    with open(os.path.join(folder, "trace.json")) as f:
        steps = json.load(f)

    md = "# UI Walkthrough\n\n"
    for i, step in enumerate(steps):
        md += f"## Step {i+1}\n"
        md += f"**Thought:** {step.get('thought', '')}\n\n"
        md += f"**Action:** {step.get('action', '')} → `{step.get('selector', '')}`\n\n"
        md += f"![Step {i}](step_{i}.png)\n\n"

    with open(os.path.join(folder, "trace.md"), "w") as f:
        f.write(md)

    print(f" Markdown guide created at {folder}/trace.md")

if __name__ == "__main__":
    import sys
    trace_to_markdown(sys.argv[1])
