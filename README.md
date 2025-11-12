# AUTONOMOUS WEB AGENT

A dual-agent that turns natural language prompts into autonomous browser runs. Agent A validates and queues requests, the planner translates them into a deterministic plan, and Agent B executes the workflow through [browser-use](https://github.com/browser-use/browser-use) with full telemetry and artifact capture.

## Highlights

- 🔀 **Two-agent workflow:** Agent A sanitizes prompts and tracks status while Agent B performs the live browser automation.
- 🧠 **Structured planning:** `planner.py` calls GPT‑4o to create JSON plans (objective, steps, success criteria) before any browser action.
- 🖥️ **FastAPI dashboard:** `server.py` + `templates/index.html` provide a glassmorphism UI with live task polling and artifact links.
- 📦 **Artifact trail:** Every run writes traces, plans, JSON metadata, and per-step screenshots under `exports/run_*`.

## Requirements

- Python 3.11+
- Google Chrome/Chromium (recommended) or the default browser-use Chromium build
- API keys:
  - `OPENAI_API_KEY` for planning
  - `BROWSER_USE_API_KEY` for BrowserUse/LLM control

## Setup

### 1. Install dependencies

```bash
git clone <repo-url>
cd multiagent
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the project root (loaded via `python-dotenv`). At minimum you need:

```env
# Planning LLM
OPENAI_API_KEY=sk-your-openai-key

# BrowserUse LLM (bu-1-0 / Anthropic via browser-use)
BROWSER_USE_API_KEY=bu_your_key

# Optional: point BrowserUse to an installed Chrome profile, this is for authentication(complicated becuase of Google CDP update)
CHROME_EXECUTABLE="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CHROME_USER_DATA_DIR=~/browser-profiles/browser-use #new profile created only for browseruse
CHROME_PROFILE_DIRECTORY=browser-control #basically your profile here
BROWSER_HEADLESS=false
BROWSER_EXTRA_ARGS=--disable-notifications
```

Any variable can be omitted to fall back to BrowserUse’s managed Chromium. `BROWSER_HEADLESS` accepts `true`/`false`. `BROWSER_EXTRA_ARGS` is a space-delimited list fed directly to Chrome. `MAX_CONCURRENT_RUNS` caps how many BrowserUse sessions can execute at once (defaults to 2).

### 3. Create a fresh Chrome profile for the agent

Running automations against your primary profile is buggy and risks cross-contamination. To create a dedicated profile:

1. Pick a user-data directory, e.g. `~/browser-profiles/browser-use`. Ensure the directory exists.
2. Launch Chrome manually with that directory to bootstrap a brand-new profile. Examples:

   **macOS / Linux**
   ```bash
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
     --user-data-dir=~/browser-profiles/browser-use \
     --profile-directory=browser-control
   ```

   **Windows (PowerShell)**
   ```powershell
   & "C:\Program Files\Google\Chrome\Application\chrome.exe" `
     --user-data-dir="$env:USERPROFILE\browser-profiles\browser-use" `
     --profile-directory=browser-control
   ```

3. Sign out of any personal accounts if prompted, set desired defaults (extensions, zoom, language), then close Chrome.
4. Copy the same paths into `.env` as shown above (`CHROME_USER_DATA_DIR`, `CHROME_PROFILE_DIRECTORY`). The automation agent will now reuse that isolated context.

If you ever need to reset the profile, simply delete the chosen directory and repeat the bootstrap command.( This is currently done because Browseruse has issues with google CDP, another way is cookie session which can implemented to overcome this)

## Running the agents

### Run the application

```bash
uvicorn server:app --reload --port 8000
```

- Visit `http://localhost:8000` for the landing overview.
- Jump into `http://localhost:8000/control` for the live agent page.
- `/api/tasks` exposes JSON for external tooling.
- `/api/metrics` reports averages/counts for the hero widgets and external monitoring.

## Artifacts & downloads

- `exports/run_*`: trace JSON, plan JSON, run metadata, animated GIF (`agent_history.gif`), and per-step screenshots (`step_n.png`).
- `agent_history.gif` at the repo root is overwritten with the latest run when `generate_gif` is enabled.
- Download watchdog logs (from `browser_use`) surface in the console.

## Project structure

```
agent_A.py        # Task intake + TaskRecord dataclass
agent_B.py        # BrowserUse orchestration, artifact saving, Chrome profile wiring
planner.py        # GPT-4o planning + plan rendering
server.py         # FastAPI API + UI endpoints
static/           # app.js + styles for the dashboard
templates/        # Jinja2 templates (index.html)
exports/          # Generated artifacts (gitignored)
run.py            # CLI entrypoint
```
