const out = document.getElementById("out");
const actionsEl = document.getElementById("actions");
const tabsEl = document.getElementById("tabs");
const fieldsEl = document.getElementById("fields");
const summaryEl = document.getElementById("summary");
let actions = [];
let currentGroup = "";
let currentAction = null;

function show(value) {
  out.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

async function api(path, options = {}) {
  const response = await fetch(path, { credentials: "same-origin", ...options });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || data.message || response.statusText);
  }
  return data;
}

function renderSummary(summary) {
  if (!summary) {
    summaryEl.innerHTML = "";
    return;
  }
  summaryEl.innerHTML = [
    `登录态：${summary.logged_in ? "已登录" : "未登录"}`,
    `Cookie 字段：${summary.cookie_fields}`,
    `msToken：${summary.has_ms_token ? "有" : "无"}`,
    `UIFID：${summary.has_uifid ? "有" : "无"}`,
    `ticket-guard：${summary.has_ticket_guard ? "有" : "无"}`,
  ].map((line) => `<div>${line}</div>`).join("");
}

function setStatus(imported, summary) {
  document.getElementById("status-dot").classList.toggle("on", imported);
  document.getElementById("status-text").textContent = imported
    ? (summary?.logged_in ? "已导入，已登录" : "已导入，未检测到登录 Cookie")
    : "未导入会话";
  renderSummary(summary);
}

function groups() {
  return [...new Set(actions.map((item) => item.group))];
}

function renderTabs() {
  tabsEl.innerHTML = "";
  for (const group of groups()) {
    const button = document.createElement("button");
    button.className = `tab${group === currentGroup ? " active" : ""}`;
    button.textContent = group;
    button.onclick = () => {
      currentGroup = group;
      renderTabs();
      renderActions();
    };
    tabsEl.appendChild(button);
  }
}

function renderActions() {
  actionsEl.innerHTML = "";
  for (const item of actions.filter((row) => row.group === currentGroup)) {
    const button = document.createElement("button");
    button.className = `action${currentAction?.id === item.id ? " active" : ""}`;
    button.innerHTML = `${item.label}${item.write ? ' <span class="write">写</span>' : ""}<small>${item.id}</small>`;
    button.onclick = () => {
      currentAction = item;
      renderActions();
      renderFields();
    };
    actionsEl.appendChild(button);
  }
}

function renderFields() {
  fieldsEl.innerHTML = "";
  if (!currentAction) return;
  for (const field of currentAction.fields) {
    const label = document.createElement("label");
    label.textContent = field.label + (field.required ? " *" : "");
    const input = document.createElement("input");
    input.name = field.name;
    input.placeholder = field.placeholder || field.name;
    input.value = field.value || "";
    fieldsEl.append(label, input);
  }
}

document.getElementById("import-btn").onclick = async () => {
  try {
    const data = await api("/api/session", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        cookie: document.getElementById("cookie").value,
        user_agent: document.getElementById("ua").value,
        webid: document.getElementById("webid").value,
        device_id: document.getElementById("webid").value,
      }),
    });
    document.getElementById("cookie").value = "";
    setStatus(true, data.summary);
    show({ imported: true, summary: data.summary });
  } catch (error) {
    show({ error: error.message });
  }
};

document.getElementById("clear-btn").onclick = async () => {
  await api("/api/session", { method: "DELETE" });
  setStatus(false);
  show("会话已清除");
};

document.getElementById("run-btn").onclick = async () => {
  if (!currentAction) {
    show("请选择一个接口");
    return;
  }
  const args = {};
  for (const input of fieldsEl.querySelectorAll("input")) {
    args[input.name] = input.value;
  }
  try {
    const data = await api("/api/call", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ action: currentAction.id, args }),
    });
    show(data);
  } catch (error) {
    show({ error: error.message });
  }
};

document.getElementById("publish-btn").onclick = async () => {
  const files = document.getElementById("pub-files").files;
  if (!files.length) {
    show("请选择媒体文件");
    return;
  }
  const form = new FormData();
  form.append("kind", document.getElementById("pub-kind").value);
  form.append("text", document.getElementById("pub-text").value);
  form.append("visibility_type", document.getElementById("pub-vis").value);
  for (const file of files) form.append("files", file);
  try {
    const response = await fetch("/api/publish", { method: "POST", body: form, credentials: "same-origin" });
    const data = await response.json();
    show(data);
  } catch (error) {
    show({ error: error.message });
  }
};

(async function boot() {
  const catalog = await api("/api/actions");
  actions = catalog.actions;
  currentGroup = groups()[0];
  currentAction = actions[0];
  renderTabs();
  renderActions();
  renderFields();
  const session = await api("/api/session");
  setStatus(session.imported, session.summary);
  if (!session.imported) show("导入 Cookie 后即可调用接口。");
})();
