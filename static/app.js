const form = document.getElementById("task-form");
const promptInput = document.getElementById("prompt");
const statusEl = document.getElementById("form-status");
const taskList = document.getElementById("task-list");
const refreshButton = document.getElementById("refresh-button");
const metricEls = {
  avgRuntime: document.querySelector('[data-metric="avg-runtime"]'),
  successCount: document.querySelector('[data-metric="success-count"]'),
  latestExport: document.querySelector('[data-metric="latest-export"]'),
};

async function submitTask(event) {
  event.preventDefault();
  const prompt = promptInput.value.trim();
  if (!prompt) {
    statusEl.textContent = "Please describe the task.";
    return;
  }

  statusEl.textContent = "Submitting…";
  try {
    const response = await fetch("/api/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || "Request failed");
    }

    promptInput.value = "";
    statusEl.textContent = "Queued! Agent B will start shortly.";
    await refreshTasks();
  } catch (error) {
    console.error(error);
    statusEl.textContent = `Error: ${error.message}`;
  }
}

function renderTask(task) {
  const container = document.createElement("article");
  container.className = `task task--${task.status}`;
  container.innerHTML = `
    <header>
      <h3>${task.prompt}</h3>
      <span class="status-pill status-pill--${task.status}">${task.status}</span>
    </header>
    <p class="meta">Requested at: ${new Date(task.created_at).toLocaleString()}</p>
    ${task.export_path ? `<p class="meta">Artifacts: <code>${task.export_path}</code></p>` : ""}
    ${task.plan ? `<details><summary>Plan JSON</summary><pre>${JSON.stringify(task.plan, null, 2)}</pre></details>` : ""}
    ${task.error ? `<p class="error">Error: ${task.error}</p>` : ""}
  `;
  return container;
}

async function refreshTasks() {
  try {
    const response = await fetch("/api/tasks");
    if (!response.ok) {
      throw new Error("Could not load tasks");
    }
    const data = await response.json();
    taskList.innerHTML = "";
    data
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      .forEach((task) => taskList.appendChild(renderTask(task)));
  } catch (error) {
    console.error(error);
    statusEl.textContent = `Refresh failed: ${error.message}`;
  }
}

function formatDuration(seconds) {
  if (!Number.isFinite(seconds)) {
    return "—";
  }
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${minutes}m ${secs.toString().padStart(2, "0")}s`;
}

function formatRelativeTime(isoString) {
  if (!isoString) {
    return "—";
  }
  const timestamp = new Date(isoString);
  if (Number.isNaN(timestamp.getTime())) {
    return "—";
  }
  const diffMs = Date.now() - timestamp.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  if (diffSeconds < 60) {
    return "moments ago";
  }
  const diffMinutes = Math.floor(diffSeconds / 60);
  if (diffMinutes < 60) {
    return `${diffMinutes}m ago`;
  }
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

async function refreshMetrics() {
  try {
    const response = await fetch("/api/metrics");
    if (!response.ok) {
      throw new Error("Could not load metrics");
    }
    const data = await response.json();
    if (metricEls.avgRuntime) {
      metricEls.avgRuntime.textContent = formatDuration(data.avg_runtime_seconds);
    }
    if (metricEls.successCount) {
      metricEls.successCount.textContent = data.success_count ?? "0";
    }
    if (metricEls.latestExport) {
      metricEls.latestExport.textContent = formatRelativeTime(data.latest_export_finished_at);
    }
  } catch (error) {
    console.error(error);
  }
}

form.addEventListener("submit", submitTask);
refreshTasks();
refreshMetrics();
setInterval(() => {
  refreshTasks();
  refreshMetrics();
}, 4000);
refreshButton?.addEventListener("click", () => refreshTasks());
