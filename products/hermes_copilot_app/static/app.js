/**
 * Hermes Copilot Core Client Application
 * Handles SSE streaming tokens, agent council selection,
 * accelerator execution, markdown parsing, and self-healing telemetry.
 */

const STATE = {
  currentAgent: "maxx",
  currentModel: "sovereign-hermes:latest",
  agents: {},
  models: [],
  isStreaming: false,
  health: {}
};

// DOM Elements
const agentListEl = document.getElementById("agentList");
const modelSelectEl = document.getElementById("modelSelect");
const chatStreamEl = document.getElementById("chatStream");
const chatInputEl = document.getElementById("chatInput");
const sendBtnEl = document.getElementById("sendBtn");
const healthBadgeEl = document.getElementById("healthBadge");
const latencyTextEl = document.getElementById("latencyText");
const inspectorDrawerEl = document.getElementById("inspectorDrawer");
const inspectorContentEl = document.getElementById("inspectorContent");
const inspectorTitleEl = document.getElementById("inspectorTitle");

// Initialize Application
async function initApp() {
  await loadAgents();
  await loadModels();
  await checkHealth();
  setInterval(checkHealth, 8000);

  // Textarea auto-resize & enter to submit
  chatInputEl.addEventListener("input", autoResizeInput);
  chatInputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  sendBtnEl.addEventListener("click", sendMessage);
}

// Auto-expand input height
function autoResizeInput() {
  chatInputEl.style.height = "auto";
  chatInputEl.style.height = Math.min(chatInputEl.scrollHeight, 180) + "px";
}

// Fetch Agents from Backend
async function loadAgents() {
  try {
    const res = await fetch("/api/agents");
    const data = await res.json();
    if (data.status === "success") {
      STATE.agents = data.agents;
      renderAgentRoster();
    }
  } catch (err) {
    console.error("Failed to load agents:", err);
  }
}

// Render Agent Sidebar
function renderAgentRoster() {
  agentListEl.innerHTML = "";
  Object.values(STATE.agents).forEach(agent => {
    const item = document.createElement("div");
    item.className = `agent-item ${agent.id === STATE.currentAgent ? "active" : ""}`;
    item.onclick = () => selectAgent(agent.id);

    item.innerHTML = `
      <div class="agent-avatar" style="background: ${agent.color};">
        ${agent.avatar}
      </div>
      <div class="agent-meta">
        <div class="agent-meta-name">${agent.name}</div>
        <div class="agent-meta-role">${agent.title}</div>
      </div>
    `;
    agentListEl.appendChild(item);
  });
}

function selectAgent(agentId) {
  STATE.currentAgent = agentId;
  renderAgentRoster();
  const agent = STATE.agents[agentId];
  if (agent) {
    appendSystemNotice(`Switched active sovereign agent to <strong>${agent.name}</strong> (${agent.role})`);
  }
}

// Fetch Available Models
async function loadModels() {
  try {
    const res = await fetch("/api/models");
    const data = await res.json();
    if (data.status === "success") {
      STATE.models = data.available_models;
      STATE.currentModel = data.active_model;
      modelSelectEl.innerHTML = "";
      STATE.models.forEach(m => {
        const opt = document.createElement("option");
        opt.value = m;
        opt.textContent = m;
        if (m === STATE.currentModel) opt.selected = true;
        modelSelectEl.appendChild(opt);
      });
    }
  } catch (err) {
    console.error("Failed to load models:", err);
  }
}

modelSelectEl.addEventListener("change", (e) => {
  STATE.currentModel = e.target.value;
  appendSystemNotice(`Active inference model updated to <code>${STATE.currentModel}</code> (bounded num_ctx: 4096)`);
});

// Periodic Health & Telemetry Check
async function checkHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    STATE.health = data;
    if (data.ollama_online) {
      healthBadgeEl.style.borderColor = "#065f46";
      healthBadgeEl.style.background = "#022c22";
      healthBadgeEl.style.color = "#34d399";
      latencyTextEl.textContent = `Online • ${data.latency_ms}ms • ${data.active_model}`;
    } else {
      healthBadgeEl.style.borderColor = "#881337";
      healthBadgeEl.style.background = "#4c0519";
      healthBadgeEl.style.color = "#fb7185";
      latencyTextEl.textContent = `Ollama Degraded • Remediation Active`;
    }
  } catch (err) {
    latencyTextEl.textContent = `Host Gateway Offline`;
  }
}

// Send Message with Real-time SSE Streaming
async function sendMessage() {
  const text = chatInputEl.value.trim();
  if (!text || STATE.isStreaming) return;

  // Intercept accelerator slash commands
  if (text.startsWith("/")) {
    chatInputEl.value = "";
    autoResizeInput();
    executeSlashCommand(text);
    return;
  }

  appendMessage("user", "You", text, null);
  chatInputEl.value = "";
  autoResizeInput();

  STATE.isStreaming = true;
  sendBtnEl.disabled = true;

  const activeAgent = STATE.agents[STATE.currentAgent] || { name: "Maxx", color: "#06b6d4" };
  const responseBubble = createStreamingBubble(activeAgent);
  chatStreamEl.appendChild(responseBubble.row);
  chatStreamEl.scrollTop = chatStreamEl.scrollHeight;

  try {
    const res = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        agent: STATE.currentAgent,
        model: STATE.currentModel,
        message: text
      })
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let accumulatedText = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split("\n\n");
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const rawJson = line.replace("data: ", "").trim();
        if (!rawJson) continue;

        try {
          const payload = JSON.parse(rawJson);
          if (payload.token) {
            accumulatedText += payload.token;
            responseBubble.contentEl.innerHTML = formatMarkdown(accumulatedText);
            chatStreamEl.scrollTop = chatStreamEl.scrollHeight;
          }
          if (payload.done) {
            responseBubble.telemetryEl.textContent = `${payload.ttft_sec}s TTFT • ${payload.tokens_per_sec} tok/s • ${payload.token_count} tokens`;
          }
          if (payload.error) {
            responseBubble.contentEl.innerHTML += `<div style="color: #ef4444; margin-top: 8px;">[Inference Error: ${payload.error}]</div>`;
          }
        } catch (e) {
          // ignore stream parse chunk split
        }
      }
    }
  } catch (err) {
    responseBubble.contentEl.innerHTML += `<div style="color: #ef4444;">[Network Error: ${err.message}]</div>`;
  } finally {
    STATE.isStreaming = false;
    sendBtnEl.disabled = false;
    attachCopyButtons(responseBubble.contentEl);
  }
}

// Execute Built-in Accelerator Tools
async function executeSlashCommand(cmdStr) {
  const parts = cmdStr.split(" ");
  const toolName = parts[0].replace("/", "").toLowerCase();
  const rest = parts.slice(1).join(" ");

  appendSystemNotice(`⚡ Executing Accelerator: <code>/${toolName}</code>`);

  try {
    let payload = { tool: toolName, params: {} };
    if (toolName === "distill") {
      payload.params = { text: rest || "Sovereign intelligence requires local unaligned models, zero cloud leakage, and invariant execution." };
    } else if (toolName === "drift") {
      payload.params = { target_dir: "." };
    } else if (toolName === "audit") {
      payload.params = {};
    } else if (toolName === "speak") {
      payload.params = { agent: STATE.currentAgent, message: rest || "Hermes Copilot Sovereign Gateway ready." };
    } else if (toolName === "heal") {
      const res = await fetch("/api/remediate", { method: "POST" });
      const data = await res.json();
      openInspector("Self-Healing Remediation Result", data);
      return;
    }

    const res = await fetch("/api/tools/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    openInspector(`Tool: /${toolName}`, result);
  } catch (err) {
    appendSystemNotice(`❌ Accelerator execution failed: ${err.message}`);
  }
}

function openInspector(title, data) {
  inspectorTitleEl.textContent = title;
  inspectorContentEl.textContent = JSON.stringify(data, null, 2);
  inspectorDrawerEl.classList.remove("collapsed");
}

function toggleInspector() {
  inspectorDrawerEl.classList.toggle("collapsed");
}

function triggerQuickTool(cmd) {
  chatInputEl.value = cmd + " ";
  chatInputEl.focus();
  autoResizeInput();
}

// UI Helpers
function appendMessage(role, senderName, text, telemetry) {
  const row = document.createElement("div");
  row.className = `message-row ${role}`;
  row.innerHTML = `
    <div class="message-bubble">
      <div class="message-header">
        <div class="msg-agent-title">${senderName}</div>
        ${telemetry ? `<div class="msg-telemetry-badge">${telemetry}</div>` : ""}
      </div>
      <div class="message-content">${formatMarkdown(text)}</div>
    </div>
  `;
  chatStreamEl.appendChild(row);
  chatStreamEl.scrollTop = chatStreamEl.scrollHeight;
  attachCopyButtons(row);
}

function createStreamingBubble(agent) {
  const row = document.createElement("div");
  row.className = "message-row assistant";
  row.innerHTML = `
    <div class="message-bubble">
      <div class="message-header">
        <div class="msg-agent-title" style="color: ${agent.color};">
          <span style="display:inline-block; width:8px; height:8px; background:${agent.color}; border-radius:50%;"></span>
          ${agent.name}
        </div>
        <div class="msg-telemetry-badge" id="telemetry">Streaming tokens...</div>
      </div>
      <div class="message-content" id="streamContent"></div>
    </div>
  `;
  return {
    row: row,
    contentEl: row.querySelector("#streamContent"),
    telemetryEl: row.querySelector("#telemetry")
  };
}

function appendSystemNotice(html) {
  const row = document.createElement("div");
  row.style.textAlign = "center";
  row.style.fontSize = "12px";
  row.style.color = "#94a3b8";
  row.style.margin = "8px 0";
  row.innerHTML = `<span>${html}</span>`;
  chatStreamEl.appendChild(row);
  chatStreamEl.scrollTop = chatStreamEl.scrollHeight;
}

// Lightweight Markdown Formatter
function formatMarkdown(src) {
  if (!src) return "";
  let out = src
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Code blocks ```lang\ncode\n```
  out = out.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<pre><code>${code.trim()}</code><button class="copy-code-btn" onclick="copyCode(this)">Copy</button></pre>`;
  });

  // Inline code `code`
  out = out.replace(/`([^`]+)`/g, '<code style="background:#1e293b; padding:2px 6px; border-radius:4px; font-family:var(--font-mono); color:#38bdf8;">$1</code>');

  // Bold **text**
  out = out.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  // Linebreaks
  out = out.replace(/\n/g, '<br/>');

  return out;
}

function attachCopyButtons(container) {
  // Handled inline via copyCode(this)
}

function copyCode(btn) {
  const codeEl = btn.parentElement.querySelector("code");
  if (codeEl) {
    navigator.clipboard.writeText(codeEl.innerText);
    const oldText = btn.textContent;
    btn.textContent = "Copied!";
    setTimeout(() => { btn.textContent = oldText; }, 2000);
  }
}

// Real-time Sovereign Neural Waveform Canvas
function initWaveformCanvas() {
  const canvas = document.createElement("canvas");
  canvas.id = "neuralWaveCanvas";
  canvas.style.position = "absolute";
  canvas.style.bottom = "80px";
  canvas.style.right = "24px";
  canvas.style.width = "200px";
  canvas.style.height = "50px";
  canvas.style.pointerEvents = "none";
  canvas.style.opacity = "0.75";
  canvas.style.zIndex = "10";
  document.querySelector(".chat-container").appendChild(canvas);

  const ctx = canvas.getContext("2d");
  let step = 0;

  function renderWave() {
    canvas.width = 200;
    canvas.height = 50;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const isStreaming = STATE.isStreaming;
    const baseAmp = isStreaming ? 16 : 4;
    const speed = isStreaming ? 0.15 : 0.04;
    step += speed;

    ctx.beginPath();
    ctx.lineWidth = 2;
    ctx.strokeStyle = isStreaming ? "#06b6d4" : "#334155";
    ctx.shadowBlur = isStreaming ? 8 : 0;
    ctx.shadowColor = "#06b6d4";

    for (let x = 0; x < canvas.width; x++) {
      const y = canvas.height / 2 + Math.sin(x * 0.05 + step) * baseAmp * Math.cos(x * 0.02 + step * 0.5);
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    requestAnimationFrame(renderWave);
  }
  renderWave();
}

// Start client on load
window.addEventListener("DOMContentLoaded", () => {
  initApp();
  initWaveformCanvas();
});
