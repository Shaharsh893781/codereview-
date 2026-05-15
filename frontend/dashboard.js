const token = localStorage.getItem("token");
const qs = (selector) => document.querySelector(selector);

if (!token) {
  window.location.href = "/";
}

qs("#logoutBtn").addEventListener("click", () => {
  localStorage.removeItem("token");
  window.location.href = "/";
});

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  headers.Authorization = `Bearer ${token}`;
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || "Request failed");
  }
  return response.json();
}

async function analyze() {
  const result = await api("/api/analyze", {
    method: "POST",
    body: JSON.stringify({ code: qs("#codeEditor").value, filename: "dashboard_input.py", language: "python" }),
  });
  renderResult(result);
  await loadHistory();
}

function renderResult(result) {
  qs("#totalIssues").textContent = result.issues.length;
  qs("#qualityScore").textContent = result.scores.quality_score;
  qs("#maintainabilityScore").textContent = result.scores.maintainability_score;
  qs("#complexityScore").textContent = result.scores.cyclomatic_complexity;

  qs("#issuesTab").innerHTML = result.issues.map(issue => `
    <article class="issue ${issue.severity}">
      <small>Line ${issue.line} | ${issue.severity.toUpperCase()} | ${issue.rule}</small>
      <strong>${escapeHtml(issue.message)}</strong>
      <p>${escapeHtml(issue.suggestion)}</p>
    </article>
  `).join("") || "<p>No issues detected.</p>";

  qs("#aiTab").innerHTML = result.ai_suggestions.map(item => `
    <article class="issue"><p>${escapeHtml(item)}</p></article>
  `).join("");
  renderCharts(result);
}

function renderCharts(result) {
  const functions = result.metrics.complexity_by_function || [];
  const labels = functions.map(item => item.name);
  const values = functions.map(item => item.complexity);
  drawBarChart(qs("#complexityChart"), labels, values, "#2dd4bf");
  drawLineChart(qs("#qualityChart"), ["Readability", "Maintainability", "Quality"], [
    result.scores.readability_score,
    result.scores.maintainability_score,
    result.scores.quality_score,
  ]);
}

function setupCanvas(canvas) {
  const width = Math.max(canvas.parentElement.clientWidth - 32, 260);
  const height = 210;
  canvas.width = width * window.devicePixelRatio;
  canvas.height = height * window.devicePixelRatio;
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;
  const context = canvas.getContext("2d");
  context.scale(window.devicePixelRatio, window.devicePixelRatio);
  context.clearRect(0, 0, width, height);
  context.font = "12px Inter, sans-serif";
  return { context, width, height };
}

function drawBarChart(canvas, labels, values, color) {
  const { context, width, height } = setupCanvas(canvas);
  const max = Math.max(...values, 1);
  const barWidth = Math.max(24, (width - 60) / Math.max(values.length, 1) - 12);
  context.fillStyle = "#9aa7bd";
  context.fillText("Function complexity", 8, 18);
  values.forEach((value, index) => {
    const x = 40 + index * (barWidth + 12);
    const barHeight = (value / max) * 130;
    context.fillStyle = color;
    context.fillRect(x, height - 34 - barHeight, barWidth, barHeight);
    context.fillStyle = "#f4f7fb";
    context.fillText(String(value), x + 4, height - 40 - barHeight);
    context.fillStyle = "#9aa7bd";
    context.fillText((labels[index] || "n/a").slice(0, 10), x, height - 12);
  });
}

function drawLineChart(canvas, labels, values) {
  const { context, width, height } = setupCanvas(canvas);
  const points = values.map((value, index) => ({
    x: 42 + index * ((width - 84) / Math.max(values.length - 1, 1)),
    y: height - 34 - (value / 100) * 140,
    value,
  }));
  context.strokeStyle = "#60a5fa";
  context.lineWidth = 3;
  context.beginPath();
  points.forEach((point, index) => index ? context.lineTo(point.x, point.y) : context.moveTo(point.x, point.y));
  context.stroke();
  points.forEach((point, index) => {
    context.fillStyle = "#60a5fa";
    context.beginPath();
    context.arc(point.x, point.y, 5, 0, Math.PI * 2);
    context.fill();
    context.fillStyle = "#f4f7fb";
    context.fillText(String(Math.round(point.value)), point.x - 8, point.y - 12);
    context.fillStyle = "#9aa7bd";
    context.fillText(labels[index], point.x - 34, height - 12);
  });
}

async function loadHistory() {
  const scans = await api("/api/scans");
  qs("#historyTab").innerHTML = scans.map(scan => `
    <article class="issue">
      <small>${new Date(scan.created_at).toLocaleString()} | ${scan.total_issues} issues</small>
      <strong>${escapeHtml(scan.filename)}</strong>
      <p>Quality ${scan.quality_score}/100, Complexity ${scan.complexity}</p>
      <button class="ghost report-btn" data-id="${scan.id}" data-kind="json" type="button">JSON</button>
      <button class="ghost report-btn" data-id="${scan.id}" data-kind="pdf" type="button">PDF</button>
    </article>
  `).join("") || "<p>No scans yet.</p>";
  document.querySelectorAll(".report-btn").forEach(button => {
    button.addEventListener("click", () => downloadReport(button.dataset.id, button.dataset.kind));
  });
}

async function downloadReport(scanId, kind) {
  const response = await fetch(`/api/scans/${scanId}/report/${kind}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error("Unable to download report");
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `scan-${scanId}.${kind}`;
  link.click();
  URL.revokeObjectURL(url);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#039;" }[char]));
}

qs("#analyzeBtn").addEventListener("click", () => analyze().catch(error => alert(error.message)));

document.querySelectorAll(".tab").forEach(tab => tab.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach(item => item.classList.remove("active"));
  tab.classList.add("active");
  document.querySelectorAll(".tab-body").forEach(body => body.classList.add("hidden"));
  qs(`#${tab.dataset.tab}Tab`).classList.remove("hidden");
}));

const dropZone = qs("#dropZone");
dropZone.addEventListener("dragover", event => {
  event.preventDefault();
  dropZone.classList.add("dragging");
});
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragging"));
dropZone.addEventListener("drop", async event => {
  event.preventDefault();
  dropZone.classList.remove("dragging");
  const file = event.dataTransfer.files[0];
  if (file) qs("#codeEditor").value = await file.text();
});

loadHistory().catch(() => {
  localStorage.removeItem("token");
  window.location.href = "/";
});
