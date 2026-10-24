let previewRows = [];
let confirmTargetId = null;
let confirmIdempotencyKey = null;
let manageTargetId = null;
let allParticipants = [];

function toast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 3200);
}

function makeIdempotencyKey(participantId) {
  return `${participantId}-${crypto.randomUUID()}`;
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || res.statusText || "Request failed");
  }
  return data;
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatJoined(iso) {
  if (!iso) return "—";
  const d = new Date(iso.includes("T") ? iso : `${iso.replace(" ", "T")}Z`);
  if (Number.isNaN(d.getTime())) return iso;
  const diff = Date.now() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days}d ago`;
  return d.toLocaleDateString();
}

function logTag(action, detail) {
  const text = `${action || ""} ${detail || ""}`.toLowerCase();
  if (text.includes("fail") || text.includes("error")) return ["error", "ERROR"];
  if (text.includes("import") || text.includes("audit")) return ["audit", "AUDIT"];
  if (text.includes("ai") || text.includes("query")) return ["info", "INFO"];
  return ["success", "SUCCESS"];
}

function renderPreview(rows) {
  const tbody = document.querySelector("#previewTable tbody");
  tbody.innerHTML = "";
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    if (!row.valid) tr.classList.add("flagged");
    tr.innerHTML = `
      <td>${escapeHtml(row.sheet_id || "—")}</td>
      <td>${escapeHtml(row.name || "")}</td>
      <td>${escapeHtml(row.email || "")}</td>
      <td>${escapeHtml(row.issue_text || "OK")}</td>
    `;
    tbody.appendChild(tr);
  });
  document.getElementById("previewWrap").classList.remove("hidden");
  const invalid = rows.filter((r) => !r.valid).length;
  document.getElementById("previewStats").textContent =
    `${rows.length} row(s), ${invalid} flagged`;
}

async function loadMeta() {
  const meta = await api("/api/event/meta");
  document.getElementById("eventTitle").textContent = meta.name;
  document.getElementById("eventDate").textContent = meta.date;
  const org = meta.organizer || "Event Organizer";
  document.getElementById("organizerName").textContent = org;
  document.getElementById("organizerInitials").textContent = org
    .split(" ")
    .map((p) => p[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

async function loadStats() {
  const s = await api("/api/dashboard/stats");
  document.getElementById("statTotal").textContent = s.total.toLocaleString();
  document.getElementById("statConfirmed").textContent = s.confirmed.toLocaleString();
  document.getElementById("statPending").textContent = s.pending.toLocaleString();
  document.getElementById("statConversion").textContent = `${s.conversion_rate}%`;
  document.getElementById("statEmailRate").textContent = `${s.email_delivery_rate}%`;
  document.getElementById("statCheckedIn").textContent = (s.checked_in ?? 0).toLocaleString();
  document.getElementById("statAttendance").textContent = `${s.attendance_rate ?? 0}%`;
}

async function loadJudgeSummary() {
  const data = await api("/api/dashboard/judge-summary");
  document.getElementById("judgeNarrative").textContent = data.narrative;
  const list = document.getElementById("judgeHighlights");
  list.innerHTML = "";
  for (const item of data.highlights || []) {
    const li = document.createElement("li");
    li.textContent = item;
    list.appendChild(li);
  }
}

async function loadActionLogs() {
  const data = await api("/api/action-logs");
  const stream = document.getElementById("logStream");
  stream.innerHTML = "";
  const logs = data.logs || [];
  if (!logs.length) {
    stream.innerHTML = '<div class="log-line"><span class="tag info">[INFO]</span>No activity yet.</div>';
    return;
  }
  for (const log of logs.slice(0, 12)) {
    const [cls, label] = logTag(log.action, log.detail);
    const time = (log.created_at || "").split(" ")[1] || log.created_at || "";
    const line = document.createElement("div");
    line.className = "log-line";
    line.innerHTML = `<span class="tag ${cls}">[${label}]</span>${escapeHtml(time)} ${escapeHtml(log.detail || log.action || "")}`;
    stream.appendChild(line);
  }
}

function passCellHtml(p) {
  if (p.pass_sent_at) {
    return '<span class="pass-pill sent">Sent</span>';
  }
  if (p.status === "confirmed") {
    return `<button type="button" class="pass-pill action btn-pass-inline" data-id="${p.id}">Send pass</button>`;
  }
  return '<span class="pass-pill pending">Not sent</span>';
}

function certCellHtml(p) {
  if (p.certificate_sent_at) {
    return '<span class="pass-pill sent">Sent</span>';
  }
  if (p.status === "confirmed") {
    return `<button type="button" class="pass-pill action btn-cert-inline" data-id="${p.id}">Send cert</button>`;
  }
  return '<span class="pass-pill pending">—</span>';
}

async function loadDashboard() {
  const search = document.getElementById("searchInput").value.trim();
  const status = document.getElementById("statusFilter").value;
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (status) params.set("status", status);
  const q = params.toString();
  const data = await api(`/api/participants${q ? `?${q}` : ""}`);
  const tbody = document.querySelector("#dashTable tbody");
  tbody.innerHTML = "";
  const rows = data.participants || [];
  allParticipants = rows;
  document.getElementById("tableFoot").textContent =
    rows.length === 0
      ? "Showing 0 participants"
      : `Showing 1 to ${rows.length} of ${rows.length} participants`;

  if (!rows.length) {
    tbody.innerHTML =
      '<tr><td colspan="7" class="empty-msg">No participants yet. Click <strong>Import participants</strong> to upload your sheet.</td></tr>';
    await loadStats();
    return;
  }

  for (const p of rows) {
    const tr = document.createElement("tr");
    const isConfirmed = p.status === "confirmed";
    tr.innerHTML = `
      <td class="participant-cell">
        <div class="name">${escapeHtml(p.name)}</div>
        <div class="email">${escapeHtml(p.email)}</div>
        ${p.sheet_id ? `<div class="sheet-id">ID ${escapeHtml(p.sheet_id)}</div>` : ""}
      </td>
      <td><span class="badge ${p.status}">${p.status === "pending" ? "Pending" : "Confirmed"}</span></td>
      <td>${passCellHtml(p)}</td>
      <td>${certCellHtml(p)}</td>
      <td>${
        p.checked_in_at
          ? '<span class="att-ok">Checked in</span>'
          : '<span class="att-pending">—</span>'
      }</td>
      <td>${escapeHtml(formatJoined(p.created_at))}</td>
      <td class="action-cell">
        ${
          isConfirmed
            ? `<button type="button" class="btn btn-ghost btn-sm btn-manage" data-id="${p.id}">Manage</button>`
            : `<button type="button" class="btn btn-primary btn-sm btn-confirm" data-id="${p.id}">Confirm</button>`
        }
      </td>
    `;
    tbody.appendChild(tr);
  }

  tbody.querySelectorAll(".btn-confirm").forEach((btn) => {
    btn.addEventListener("click", () => openConfirmModal(Number(btn.dataset.id)));
  });
  tbody.querySelectorAll(".btn-manage").forEach((btn) => {
    btn.addEventListener("click", () => openManageModal(Number(btn.dataset.id)));
  });
  tbody.querySelectorAll(".btn-pass-inline").forEach((btn) => {
    btn.addEventListener("click", () => postAction(Number(btn.dataset.id), "send-pass", "Pass"));
  });
  tbody.querySelectorAll(".btn-cert-inline").forEach((btn) => {
    btn.addEventListener("click", () =>
      postAction(Number(btn.dataset.id), "send-certificate", "Certificate")
    );
  });

  await loadStats();
}

async function postAction(participantId, pathSuffix, label) {
  const key = makeIdempotencyKey(`${pathSuffix}-${participantId}`);
  try {
    const data = await api(`/api/participants/${participantId}/${pathSuffix}`, {
      method: "POST",
      body: JSON.stringify({ idempotency_key: key }),
    });
    const d = data.email_delivery || {};
    toast(
      data.already_done
        ? `${label} already sent (idempotent)`
        : d.detail || `${label} completed`
    );
    await refreshAll();
  } catch (err) {
    toast(err.message || `${label} failed`);
  }
}

function openManageModal(participantId) {
  const p = allParticipants.find((x) => x.id === participantId);
  if (!p) return;
  manageTargetId = participantId;
  document.getElementById("manageWho").textContent = `${p.name} · ${p.email}`;
  document.querySelector(".btn-manage-confirm").disabled = p.status === "confirmed";
  document.getElementById("manageModal").showModal();
}

async function openConfirmModal(participantId) {
  confirmTargetId = participantId;
  confirmIdempotencyKey = makeIdempotencyKey(`confirm-${participantId}`);
  const preview = await api(`/api/participants/${participantId}/email-preview`);
  const previewEl = document.getElementById("emailPreviewBody");
  if (preview.html) {
    previewEl.innerHTML = `<div class="email-preview-meta">To: ${escapeHtml(preview.to)}<br/>Subject: ${escapeHtml(preview.subject)}</div>${preview.html}`;
  } else {
    previewEl.textContent = `To: ${preview.to}\nSubject: ${preview.subject}\n\n${preview.body}`;
  }
  document.getElementById("emailModal").showModal();
}

document.getElementById("btnOpenImport").addEventListener("click", () => {
  document.getElementById("importModal").showModal();
});
document.getElementById("btnCloseImport").addEventListener("click", () => {
  document.getElementById("importModal").close();
});

document.getElementById("uploadForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const file = document.getElementById("fileInput").files[0];
  if (!file) return;
  try {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch("/api/upload/preview", { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Upload failed");
    previewRows = data.rows || [];
    if (!previewRows.length) {
      toast("No rows found — need name and email columns");
      return;
    }
    renderPreview(previewRows);
  } catch (err) {
    toast(err.message || "Upload failed");
  }
});

async function saveRows(skipInvalid) {
  if (!previewRows.length) {
    toast("Preview a file first");
    return;
  }
  const result = await api("/api/participants/save", {
    method: "POST",
    body: JSON.stringify({
      rows: previewRows.map((r) => ({
        sheet_id: r.sheet_id || null,
        name: r.name,
        email: r.email,
      })),
      skip_invalid: skipInvalid,
    }),
  });
  toast(`Imported ${result.inserted} row(s), skipped ${result.skipped}`);
  previewRows = [];
  document.getElementById("previewWrap").classList.add("hidden");
  document.getElementById("importModal").close();
  await refreshAll();
}

document.getElementById("btnSaveValid").addEventListener("click", () => saveRows(true));
document.getElementById("btnSaveAll").addEventListener("click", () => saveRows(false));
document.getElementById("btnRefresh").addEventListener("click", refreshAll);
document.getElementById("btnRefreshSummary").addEventListener("click", () =>
  loadJudgeSummary().catch((e) => toast(e.message))
);
document.getElementById("btnBulkPasses").addEventListener("click", async () => {
  try {
    const r = await api("/api/bulk/send-passes", { method: "POST", body: "{}" });
    toast(`Bulk pass send: ${r.sent} sent, ${r.failed} failed (${r.queued} queued)`);
    await refreshAll();
    await loadJudgeSummary();
  } catch (e) {
    toast(e.message || "Bulk send failed");
  }
});
document.getElementById("btnRefreshLogs").addEventListener("click", loadActionLogs);
document.getElementById("searchInput").addEventListener("input", debounce(loadDashboard, 300));
document.getElementById("statusFilter").addEventListener("change", loadDashboard);

document.getElementById("nlForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const query = document.getElementById("nlInput").value.trim();
  const data = await api("/api/query", {
    method: "POST",
    body: JSON.stringify({ query }),
  });
  if (data.error) {
    document.getElementById("nlOutput").textContent = JSON.stringify(
      { error: data.error, hint: "Check GEMINI_API_KEY or try again later." },
      null,
      2
    );
    return;
  }
  document.getElementById("nlOutput").textContent = JSON.stringify(data, null, 2);
});

document.getElementById("btnCancelConfirm").addEventListener("click", () => {
  document.getElementById("emailModal").close();
});

document.getElementById("emailModalForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!confirmTargetId || !confirmIdempotencyKey) return;
  const data = await api(`/api/participants/${confirmTargetId}/confirm`, {
    method: "POST",
    body: JSON.stringify({ idempotency_key: confirmIdempotencyKey }),
  });
  document.getElementById("emailModal").close();
  const d = data.email_delivery || {};
  toast(
    data.already_done
      ? "Already confirmed"
      : d.detail || "Registration confirmed — email 1/3 sent"
  );
  await refreshAll();
});

document.getElementById("btnCloseManage").addEventListener("click", () => {
  document.getElementById("manageModal").close();
});
document.querySelector(".btn-manage-confirm").addEventListener("click", () => {
  if (!manageTargetId) return;
  document.getElementById("manageModal").close();
  openConfirmModal(manageTargetId);
});
document.querySelector(".btn-manage-pass").addEventListener("click", () => {
  if (!manageTargetId) return;
  document.getElementById("manageModal").close();
  postAction(manageTargetId, "send-pass", "Pass");
});
document.querySelector(".btn-manage-cert").addEventListener("click", () => {
  if (!manageTargetId) return;
  document.getElementById("manageModal").close();
  postAction(manageTargetId, "send-certificate", "Certificate");
});

function debounce(fn, ms) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

async function loadEmailStatus() {
  const data = await api("/api/email/status");
  const el = document.getElementById("emailStatus");
  el.classList.remove("live", "dry");
  if (data.connected) {
    el.textContent = `SMTP connected · ${data.from_address}`;
    el.classList.add("live");
  } else {
    el.textContent = "SMTP not configured";
    el.classList.add("dry");
  }
}

async function refreshAll() {
  await loadDashboard();
  await loadActionLogs();
}

Promise.all([loadMeta(), loadEmailStatus(), loadJudgeSummary(), refreshAll()]).catch((err) =>
  toast(err.message)
);
