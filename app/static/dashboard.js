const API_BASE = ""; // same origin

let outcomesChart = null;
let sentimentChart = null;

function $(id) { return document.getElementById(id); }

function showError(msg) {
  const el = $("errorBanner");
  el.textContent = msg;
  el.classList.remove("hidden");
}
function clearError() {
  const el = $("errorBanner");
  el.textContent = "";
  el.classList.add("hidden");
}

function apiKey() {
  const v = $("apiKey").value.trim();
  return v || "demo-key";
}

async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "x-api-key": apiKey() },
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${txt}`);
  }
  return res.json();
}

function fmtPct(x) {
  if (x === null || x === undefined) return "—";
  return `${Math.round(x * 100)}%`;
}

function fmtTs(sec) {
  if (!sec) return "—";
  // ended_at in your API looks like unix seconds (float)
  const ms = Math.floor(Number(sec) * 1000);
  const d = new Date(ms);
  return d.toLocaleString();
}

function setActiveTab(tab) {
  // buttons
  document.querySelectorAll(".tab-btn").forEach(btn => {
    const is = btn.dataset.tab === tab;
    btn.className = `tab-btn rounded-lg px-4 py-2 text-sm border ${is ? "bg-slate-900 text-white border-slate-900" : "bg-white border-slate-200"}`;
  });

  // sections
  $("tab-overview").classList.toggle("hidden", tab !== "overview");
  $("tab-call").classList.toggle("hidden", tab !== "call");
}

function renderChart(canvasId, title, dataObj, existingChart) {
  const labels = Object.keys(dataObj);
  const data = labels.map(k => dataObj[k]);

  const ctx = document.getElementById(canvasId);
  if (existingChart) existingChart.destroy();

  return new Chart(ctx, {
    type: "bar",
    data: { labels, datasets: [{ label: title, data }] },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true } }
    },
  });
}

async function loadOverview() {
  clearError();

  const [ov, outcomes, sentiment] = await Promise.all([
    apiGet("/v1/metrics/dashboard/overview"),
    apiGet("/v1/metrics/dashboard/outcomes"),
    apiGet("/v1/metrics/dashboard/sentiment"),
  ]);

  $("kpiTotal").textContent = ov.total_calls ?? "—";
  $("kpiVerified").textContent = fmtPct(ov.verified_rate);
  $("kpiAcceptance").textContent = fmtPct(ov.acceptance_rate);
  $("kpiTransfer").textContent = fmtPct(ov.transfer_rate);
  $("kpiRounds").textContent = (ov.avg_rounds ?? "—");

  outcomesChart = renderChart("chartOutcomes", "Outcomes", outcomes, outcomesChart);
  sentimentChart = renderChart("chartSentiment", "Sentiment", sentiment, sentimentChart);

  await loadCallsTable();
}

function renderCallsRows(rows) {
  const tbody = $("callsTbody");
  tbody.innerHTML = "";

  for (const r of rows) {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-50";

    const callLink = document.createElement("a");
    callLink.href = "#";
    callLink.textContent = r.call_id;
    callLink.className = "text-slate-900 font-medium underline underline-offset-2";
    callLink.onclick = (e) => {
      e.preventDefault();
      $("callIdInput").value = r.call_id;
      setActiveTab("call");
      loadCallDetail();
    };

    const tdCall = document.createElement("td");
    tdCall.className = "px-4 py-3";
    tdCall.appendChild(callLink);

    const cells = [
      tdCall,
      mkCell(fmtTs(r.ended_at)),
      mkCell(String(r.verified)),
      mkCell(r.outcome ?? "—"),
      mkCell(r.sentiment ?? "—"),
      mkCell(r.load_id ?? "—"),
      mkCell(r.rounds ?? "—"),
    ];

    for (const td of cells) tr.appendChild(td);
    tbody.appendChild(tr);
  }
}

function mkCell(text) {
  const td = document.createElement("td");
  td.className = "px-4 py-3 text-slate-700";
  td.textContent = text;
  return td;
}

async function loadCallsTable() {
  const limit = Number($("limitSelect").value || "20");
  const rows = await apiGet(`/v1/metrics/dashboard/calls?limit=${limit}`);

  const q = $("searchCallId").value.trim().toLowerCase();
  const filtered = q ? rows.filter(r => String(r.call_id).toLowerCase().includes(q)) : rows;

  renderCallsRows(filtered);
}

async function loadCallDetail() {
  clearError();
  const callId = $("callIdInput").value.trim();
  if (!callId) {
    showError("Enter a call_id.");
    return;
  }

  // This endpoint is what you already have
  const data = await apiGet(`/v1/metrics/dashboard/calls/${encodeURIComponent(callId)}`);

  $("callDashboardJson").textContent = JSON.stringify(data.dashboard ?? {}, null, 2);
  const raw = { call_state: data.call_state ?? null, raw_summary: data.raw_summary ?? null };
  $("callRawJson").textContent = JSON.stringify(raw, null, 2);
}

function wireUI() {
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => setActiveTab(btn.dataset.tab));
  });

  $("refreshBtn").addEventListener("click", async () => {
    try { await loadOverview(); }
    catch (e) { showError(e.message); }
  });

  $("limitSelect").addEventListener("change", async () => {
    try { await loadCallsTable(); }
    catch (e) { showError(e.message); }
  });

  $("searchCallId").addEventListener("input", async () => {
    try { await loadCallsTable(); }
    catch (e) { showError(e.message); }
  });

  $("loadCallBtn").addEventListener("click", async () => {
    try { await loadCallDetail(); }
    catch (e) { showError(e.message); }
  });

  // default tab
  setActiveTab("overview");
}

(async function init() {
  wireUI();
  try { await loadOverview(); }
  catch (e) { showError(e.message); }
})();
