const form = document.getElementById("task-form");
const promptInput = document.getElementById("prompt");
const statusEl = document.getElementById("form-status");
const taskList = document.getElementById("task-list");

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

form.addEventListener("submit", submitTask);
refreshTasks();
setInterval(refreshTasks, 4000);
