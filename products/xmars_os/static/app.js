/**
 * XORAS // XMARS.os Unified Client Engine
 * Unifies Hermes (Cognitive & Voice), Cursor (Workspace Editor & Terminal),
 * and Lovable (Interactive Live Visual Canvas Sandbox).
 */

const STATE = {
  currentAgent: "maxx",
  currentModel: "cf-deepseek-r1-32b",
  agents: {},
  models: [],
  activeFile: null,
  activeFileContent: "",
  activeFileType: "text",
  voiceEnabled: true,
  isRecording: false,
  recognition: null,
  isStreaming: false,
  viewportMode: "desktop",
  layoutMode: "split", // cursor, lovable, split
  workbenchMode: "composer" // composer, editor
};

// DOM References
const fileTreeContainer = document.getElementById("fileTreeContainer");
const councilListEl = document.getElementById("councilList");
const modelSelectEl = document.getElementById("modelSelect");
const healthPillEl = document.getElementById("healthPill");
const latencyLabelEl = document.getElementById("latencyLabel");

const chatStreamEl = document.getElementById("chatStream");
const composerInputEl = document.getElementById("composerInput");
const composerMicBtnEl = document.getElementById("composerMicBtn");
const voiceToggleBtnEl = document.getElementById("voiceToggleBtn");
const ctxAgentNameEl = document.getElementById("ctxAgentName");
const ctxFileTagEl = document.getElementById("ctxFileTag");
const ctxVoiceStatusEl = document.getElementById("ctxVoiceStatus");

const activeFileNameEl = document.getElementById("activeFileName");
const codeEditorAreaEl = document.getElementById("codeEditorArea");
const editorFilePathEl = document.getElementById("editorFilePath");
const editorFileStatsEl = document.getElementById("editorFileStats");
const btnSaveFileEl = document.getElementById("btnSaveFile");
const btnRunFileEl = document.getElementById("btnRunFile");
const btnPreviewCodeEl = document.getElementById("btnPreviewCode");

const previewFrameEl = document.getElementById("previewFrame");
const canvasViewportEl = document.getElementById("canvasViewport");
const terminalDrawerEl = document.getElementById("terminalDrawer");
const terminalOutputEl = document.getElementById("terminalOutput");
const terminalInputEl = document.getElementById("terminalInput");

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
  initApp();
});

async function initApp() {
  await loadCouncil();
  await loadModels();
  await loadWorkspaceTree();
  await refreshHealth();
  setInterval(refreshHealth, 8000);

  initSTT();
  initComposerInput();
  initWaveform();

  // Handle Ctrl+S for saving active file
  window.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "s") {
      e.preventDefault();
      saveActiveFile();
    }
  });
}

// --------------------------------------------------------------------------
// 1. WORKSPACE FILE EXPLORER (CURSOR MODE)
// --------------------------------------------------------------------------
async function loadWorkspaceTree() {
  fileTreeContainer.innerHTML = `<div class="tree-loading">Scanning SSOT Workspace...</div>`;
  try {
    const res = await fetch("/api/workspace/tree");
    const data = await res.json();
    if (data.status === "success" && data.tree) {
      renderFileTree(data.tree, fileTreeContainer);
    } else {
      fileTreeContainer.innerHTML = `<div style="color:#ef4444; padding:8px;">Failed to scan workspace.</div>`;
    }
  } catch (err) {
    fileTreeContainer.innerHTML = `<div style="color:#ef4444; padding:8px;">Error: ${err.message}</div>`;
  }
}

function renderFileTree(nodes, container) {
  container.innerHTML = "";
  nodes.forEach(node => {
    const item = document.createElement("div");
    item.className = "tree-item";

    if (node.type === "directory") {
      const folderHeader = document.createElement("div");
      folderHeader.className = "tree-node";
      folderHeader.innerHTML = `<span>📁</span> <strong>${node.name}</strong>`;

      const childrenBox = document.createElement("div");
      childrenBox.className = "tree-folder-children";
      childrenBox.style.display = "none";

      folderHeader.onclick = () => {
        const isHidden = childrenBox.style.display === "none";
        childrenBox.style.display = isHidden ? "block" : "none";
        folderHeader.querySelector("span").textContent = isHidden ? "📂" : "📁";
      };

      if (node.children && node.children.length > 0) {
        renderFileTree(node.children, childrenBox);
      }

      item.appendChild(folderHeader);
      item.appendChild(childrenBox);
    } else {
      const fileNode = document.createElement("div");
      fileNode.className = `tree-node ${STATE.activeFile === node.path ? "active-file" : ""}`;
      const extIco = getFileIcon(node.name);
      fileNode.innerHTML = `<span>${extIco}</span> <span>${node.name}</span>`;

      fileNode.onclick = () => openFileInEditor(node.path);
      item.appendChild(fileNode);
    }

    container.appendChild(item);
  });
}

function getFileIcon(filename) {
  if (filename.endsWith(".py")) return "🐍";
  if (filename.endsWith(".rs")) return "🦀";
  if (filename.endsWith(".js") || filename.endsWith(".ts")) return "📜";
  if (filename.endsWith(".html")) return "🌐";
  if (filename.endsWith(".css")) return "🎨";
  if (filename.endsWith(".json")) return "⚙️";
  if (filename.endsWith(".md")) return "📄";
  if (filename.endsWith(".sh") || filename.endsWith(".bat") || filename.endsWith(".ps1")) return "⚡";
  return "📄";
}

function filterFiles() {
  const query = document.getElementById("fileSearchInput").value.toLowerCase().trim();
  const allNodes = fileTreeContainer.querySelectorAll(".tree-node");
  allNodes.forEach(node => {
    const text = node.textContent.toLowerCase();
    if (!query || text.includes(query)) {
      node.style.display = "flex";
    } else {
      node.style.display = "none";
    }
  });
}

// Open File in Editor
async function openFileInEditor(relPath) {
  try {
    const res = await fetch(`/api/workspace/read?path=${encodeURIComponent(relPath)}`);
    const data = await res.json();
    if (data.status === "success") {
      STATE.activeFile = relPath;
      STATE.activeFileContent = data.content;
      STATE.activeFileType = data.extension;

      activeFileNameEl.textContent = relPath.split("/").pop();
      editorFilePathEl.textContent = `/${relPath}`;
      editorFileStatsEl.textContent = `${data.lines} lines • ${Math.round(data.size / 1024)} KB`;

      codeEditorAreaEl.value = data.content;
      btnSaveFileEl.style.display = "inline-flex";
      btnRunFileEl.style.display = "inline-flex";

      if (data.extension === ".html" || data.extension === ".md") {
        btnPreviewCodeEl.style.display = "inline-flex";
      } else {
        btnPreviewCodeEl.style.display = "none";
      }

      ctxFileTagEl.innerHTML = `File: <strong>${relPath.split("/").pop()}</strong>`;
      switchWorkbenchMode("editor");

      // Update tree active node
      document.querySelectorAll(".tree-node").forEach(n => n.classList.remove("active-file"));
    }
  } catch (err) {
    alert(`Could not open ${relPath}: ${err.message}`);
  }
}

// Save Active File
async function saveActiveFile() {
  if (!STATE.activeFile) return;
  const content = codeEditorAreaEl.value;
  try {
    const res = await fetch("/api/workspace/write", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: STATE.activeFile, content })
    });
    const data = await res.json();
    if (data.status === "success") {
      btnSaveFileEl.textContent = "Saved! ✔";
      setTimeout(() => { btnSaveFileEl.textContent = "💾 Save"; }, 1500);
      printTerminal(`[SAVE] File updated: ${STATE.activeFile} (${content.length} bytes, SHA256: ${data.sha256.slice(0, 10)})`, "prompt");
    } else {
      alert(`Save error: ${data.message}`);
    }
  } catch (err) {
    alert(`Save failed: ${err.message}`);
  }
}

function runActiveFileInTerminal() {
  if (!STATE.activeFile) return;
  toggleTerminal(true);
  if (STATE.activeFile.endsWith(".py")) {
    executeCommand(`python ${STATE.activeFile}`);
  } else if (STATE.activeFile.endsWith(".rs")) {
    executeCommand(`cargo test`);
  } else {
    executeCommand(`type ${STATE.activeFile.replace(/\//g, '\\')}`);
  }
}

function previewCurrentEditorCode() {
  const content = codeEditorAreaEl.value;
  renderToLovableCanvas(content);
}

// --------------------------------------------------------------------------
// 2. HERMES AI COMPOSER (STREAMING REASONING & VOICE)
// --------------------------------------------------------------------------
function initComposerInput() {
  composerInputEl.addEventListener("input", () => {
    composerInputEl.style.height = "auto";
    composerInputEl.style.height = Math.min(composerInputEl.scrollHeight, 160) + "px";
  });

  composerInputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      dispatchComposer();
    }
  });
}

async function dispatchComposer() {
  const text = composerInputEl.value.trim();
  if (!text || STATE.isStreaming) return;

  composerInputEl.value = "";
  composerInputEl.style.height = "auto";

  // Append user bubble
  appendChatBubble("user", text, "Anthony");

  // Create empty assistant response container
  const assistantCard = appendChatBubble("assistant", "", STATE.agents[STATE.currentAgent]?.name || "Maxx");
  const contentDiv = assistantCard.querySelector(".msg-content");
  contentDiv.innerHTML = `<span class="pulse-indicator" style="display:inline-block;"></span> <em class="reasoning-text">Reasoning with ${STATE.currentModel}...</em>`;

  STATE.isStreaming = true;

  const payload = {
    agent: STATE.currentAgent,
    model: STATE.currentModel,
    message: text,
    active_file: STATE.activeFile || "",
    voice: STATE.voiceEnabled
  };

  try {
    const res = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok || !res.body) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let accumulated = "";
    let buffer = "";
    let firstTokenReceived = false;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop();

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data:")) continue;
        const dataStr = trimmed.slice(5).trim();
        try {
          const parsed = JSON.parse(dataStr);
          if (parsed.token) {
            if (!firstTokenReceived) {
              firstTokenReceived = true;
              contentDiv.innerHTML = "";
            }
            accumulated += parsed.token;
            contentDiv.innerHTML = formatMarkdown(accumulated);
            chatStreamEl.scrollTop = chatStreamEl.scrollHeight;
          } else if (parsed.done) {
            STATE.isStreaming = false;
            contentDiv.innerHTML = formatMarkdown(accumulated);
            checkAndRenderVisuals(accumulated);
            chatStreamEl.scrollTop = chatStreamEl.scrollHeight;
            if (parsed.tokens_per_sec) {
              const metaTag = document.createElement("div");
              metaTag.style.cssText = "font-size:10px; color:#64748b; margin-top:6px; font-family:monospace;";
              metaTag.textContent = `⚡ ${parsed.tokens_per_sec} tok/s • ${parsed.total_sec || parsed.latency_sec || 0}s • ${parsed.model || STATE.currentModel}`;
              contentDiv.appendChild(metaTag);
            }
          }
        } catch (e) {
          // ignore json parse err on partial line
        }
      }
    }

    STATE.isStreaming = false;
    if (!accumulated && !firstTokenReceived) {
      contentDiv.innerHTML = `<span style="color:#ef4444;">No response received from kernel.</span>`;
    } else {
      checkAndRenderVisuals(accumulated);
    }
  } catch (err) {
    STATE.isStreaming = false;
    contentDiv.innerHTML = `<span style="color:#ef4444;">Stream Error: ${err.message}</span>`;
  }
}

function appendChatBubble(role, rawContent, senderName) {
  const card = document.createElement("div");
  card.className = `msg-bubble ${role}`;

  const agent = STATE.agents[STATE.currentAgent] || { color: "#06b6d4", avatar: "M", title: "Sovereign AI" };
  const avatarBg = role === "user" ? "#3b82f6" : agent.color;
  const avatarLetter = role === "user" ? "A" : agent.avatar;
  const title = role === "user" ? "Sovereign Operator" : agent.title;

  card.innerHTML = `
    <div class="msg-meta">
      <span class="agent-avatar" style="background:${avatarBg};">${avatarLetter}</span>
      <span class="agent-name" style="color:${avatarBg};">${senderName}</span>
      <span class="role-badge">${title}</span>
      <span class="timestamp">${new Date().toLocaleTimeString()}</span>
    </div>
    <div class="msg-content">${rawContent ? formatMarkdown(rawContent) : ""}</div>
  `;

  chatStreamEl.appendChild(card);
  chatStreamEl.scrollTop = chatStreamEl.scrollHeight;
  return card;
}

function formatMarkdown(text) {
  if (!text) return "";
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Code blocks: ```lang ... ```
  html = html.replace(/```([a-zA-Z0-9_\-\.]*)\n([\s\S]*?)```/g, (match, lang, code) => {
    const unescapedCode = code.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
    const isVisual = lang === "html" || lang === "jsx" || lang === "svg" || unescapedCode.includes("<div") || unescapedCode.includes("<!DOCTYPE");
    
    return `
      <pre><div class="code-action-bar">
        <span style="margin-right:auto; font-size:10px; color:#64748b; text-transform:uppercase;">${lang || 'code'}</span>
        <button class="code-act-btn" onclick="copyCodeSnippet(this)">Copy</button>
        ${isVisual ? `<button class="code-act-btn" style="color:#00f0ff; border-color:#00f0ff;" onclick="renderSnippetToCanvas(this)">🎨 Render in Canvas</button>` : ''}
        <button class="code-act-btn" onclick="applyCodeToEditor(this)">Open in Editor</button>
      </div><code>${code}</code></pre>
    `;
  });

  // Inline code `code`
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

  // Bold & Italic
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*([^*]+)\*/g, "<em>$1</em>");

  // Collapsible Think container (DeepSeek / Reasoning models)
  html = html.replace(/&lt;think&gt;([\s\S]*?)&lt;\/think&gt;/gi, (match, thought) => {
    return `
      <details class="thought-process-container" open>
        <summary class="thought-summary">🧠 Cognitive Reasoning Trace</summary>
        <div class="thought-body">${thought.trim()}</div>
      </details>
    `;
  });
  // Handle unclosed <think> during active streaming
  html = html.replace(/&lt;think&gt;([\s\S]*)$/gi, (match, thought) => {
    return `
      <details class="thought-process-container" open>
        <summary class="thought-summary"><span class="pulse-indicator"></span> Reasoning...</summary>
        <div class="thought-body">${thought.trim()}</div>
      </details>
    `;
  });

  return html;
}

function copyCodeSnippet(btn) {
  const codeEl = btn.closest("pre").querySelector("code");
  const text = codeEl.innerText;
  navigator.clipboard.writeText(text);
  btn.textContent = "Copied! ✔";
  setTimeout(() => { btn.textContent = "Copy"; }, 1500);
}

function applyCodeToEditor(btn) {
  const codeEl = btn.closest("pre").querySelector("code");
  const text = codeEl.innerText;
  codeEditorAreaEl.value = text;
  switchWorkbenchMode("editor");
  editorFilePathEl.textContent = "Generated Snippet (Unsaved)";
  editorFileStatsEl.textContent = `${text.split("\n").length} lines`;
  btnSaveFileEl.style.display = "inline-flex";
}

function renderSnippetToCanvas(btn) {
  const codeEl = btn.closest("pre").querySelector("code");
  const text = codeEl.innerText;
  renderToLovableCanvas(text);
  if (STATE.layoutMode === "cursor") {
    setLayoutMode("split");
  }
}

function checkAndRenderVisuals(reply) {
  // If the reply contains a complete HTML document or interactive component, load it in the canvas!
  const match = reply.match(/```(?:html|jsx|xml)\n([\s\S]*?)```/);
  if (match && match[1]) {
    const raw = match[1];
    if (raw.includes("<html") || raw.includes("<div") || raw.includes("<svg") || raw.includes("<canvas")) {
      renderToLovableCanvas(raw);
    }
  }
}

// --------------------------------------------------------------------------
// 3. LOVABLE LIVE VISUAL CANVAS SANDBOX
// --------------------------------------------------------------------------
async function renderToLovableCanvas(htmlContent) {
  try {
    const res = await fetch("/api/preview/render", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ html: htmlContent })
    });
    const data = await res.json();
    if (data.status === "success") {
      previewFrameEl.src = data.preview_url + "?t=" + Date.now();
    }
  } catch (err) {
    console.error("Failed to render canvas preview:", err);
  }
}

function setViewport(mode) {
  STATE.viewportMode = mode;
  document.querySelectorAll(".vp-btn").forEach(btn => btn.classList.remove("active"));
  event.target.classList.add("active");

  canvasViewportEl.className = `canvas-viewport vp-${mode}`;
}

function reloadPreview() {
  previewFrameEl.src = previewFrameEl.src.split("?")[0] + "?t=" + Date.now();
}

function openPreviewNewTab() {
  window.open(previewFrameEl.src, "_blank");
}

// --------------------------------------------------------------------------
// 4. INTEGRATED TERMINAL CONSOLE
// --------------------------------------------------------------------------
function toggleTerminal(forceOpen = false) {
  if (forceOpen) {
    terminalDrawerEl.classList.add("active");
  } else {
    terminalDrawerEl.classList.toggle("active");
  }
  if (terminalDrawerEl.classList.contains("active")) {
    terminalInputEl.focus();
  }
}

function handleTerminalKey(e) {
  if (e.key === "Enter") {
    execTerminalInput();
  }
}

function execTerminalInput() {
  const cmd = terminalInputEl.value.trim();
  if (!cmd) return;
  terminalInputEl.value = "";
  executeCommand(cmd);
}

function runQuickCmd(cmd) {
  toggleTerminal(true);
  executeCommand(cmd);
}

async function executeCommand(cmd) {
  printTerminal(`❯ ${cmd}`, "prompt");
  try {
    const res = await fetch("/api/terminal/exec", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command: cmd })
    });
    const data = await res.json();
    if (data.stdout) printTerminal(data.stdout, "stdout");
    if (data.stderr) printTerminal(data.stderr, "stderr");
    if (data.exit_code !== 0) {
      printTerminal(`[Exited with code ${data.exit_code} in ${data.duration_sec}s]`, "stderr");
    } else {
      printTerminal(`[Command completed successfully in ${data.duration_sec}s]`, "prompt");
    }
  } catch (err) {
    printTerminal(`Terminal error: ${err.message}`, "stderr");
  }
}

function printTerminal(text, type = "stdout") {
  const line = document.createElement("div");
  line.className = `term-line ${type}`;
  line.textContent = text;
  terminalOutputEl.appendChild(line);
  terminalOutputEl.scrollTop = terminalOutputEl.scrollHeight;
}

function clearTerminal() {
  terminalOutputEl.innerHTML = "";
}

// --------------------------------------------------------------------------
// 5. COUNCIL & MODEL MANAGEMENT
// --------------------------------------------------------------------------
async function loadCouncil() {
  try {
    const res = await fetch("/api/agents");
    const data = await res.json();
    if (data.status === "success") {
      STATE.agents = data.agents;
      renderCouncilList();
    }
  } catch (err) {
    console.error("Council load failed:", err);
  }
}

function renderCouncilList() {
  councilListEl.innerHTML = "";
  Object.values(STATE.agents).forEach(agent => {
    const card = document.createElement("div");
    card.className = `council-card ${agent.id === STATE.currentAgent ? "selected" : ""}`;
    card.onclick = () => selectAgent(agent.id);

    card.innerHTML = `
      <div class="council-avatar" style="background:${agent.color};">${agent.avatar}</div>
      <div class="council-info">
        <div class="council-name">${agent.name}</div>
        <div class="council-title">${agent.title}</div>
      </div>
    `;
    councilListEl.appendChild(card);
  });
}

function selectAgent(agentId) {
  STATE.currentAgent = agentId;
  renderCouncilList();
  ctxAgentNameEl.textContent = STATE.agents[agentId]?.name || agentId;
}

async function loadModels() {
  try {
    const res = await fetch("/api/models");
    const data = await res.json();
    if (data.status === "success") {
      STATE.models = data.available_models;
    }
  } catch (err) {
    console.error("Model load failed:", err);
  }

  modelSelectEl.addEventListener("change", (e) => {
    STATE.currentModel = e.target.value;
  });
}

async function refreshHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    if (data) {
      latencyLabelEl.textContent = `Kernel Online (8085) • ${data.active_model || 'SNM-8B'}`;
      document.getElementById("hudContext").textContent = `${data.hardware_governor?.max_context_bound || 4096} Bound`;
      document.getElementById("hudPressure").textContent = data.hardware_governor?.memory_pressure || "NORMAL";
    }
  } catch (err) {
    latencyLabelEl.textContent = "Kernel Offline";
  }
}

// --------------------------------------------------------------------------
// 6. LAYOUT & NAVIGATION CONTROLS
// --------------------------------------------------------------------------
function setLayoutMode(mode) {
  STATE.layoutMode = mode;
  document.body.className = `theme-obsidian mode-${mode}`;
  document.querySelectorAll(".view-btn").forEach(btn => btn.classList.remove("active"));
  if (mode === "cursor") document.getElementById("btnModeCursor").classList.add("active");
  if (mode === "split") document.getElementById("btnModeSplit").classList.add("active");
  if (mode === "lovable") document.getElementById("btnModeLovable").classList.add("active");
}

function switchSidebarTab(tabName) {
  document.querySelectorAll(".sidebar-tabs .tab-btn").forEach((b, i) => {
    b.classList.toggle("active", (tabName === 'files' && i === 0) || (tabName === 'council' && i === 1) || (tabName === 'telemetry' && i === 2));
  });
  document.getElementById("tabFiles").classList.toggle("active", tabName === "files");
  document.getElementById("tabCouncil").classList.toggle("active", tabName === "council");
  document.getElementById("tabTelemetry").classList.toggle("active", tabName === "telemetry");
}

function switchWorkbenchMode(mode) {
  STATE.workbenchMode = mode;
  document.getElementById("tabComposer").classList.toggle("active", mode === "composer");
  document.getElementById("tabEditor").classList.toggle("active", mode === "editor");
  document.getElementById("viewComposer").classList.toggle("active", mode === "composer");
  document.getElementById("viewEditor").classList.toggle("active", mode === "editor");
}

function triggerCommand(cmd) {
  composerInputEl.value = cmd;
  dispatchComposer();
}

function copySaasLink() {
  fetch("/api/tunnel").then(r => r.json()).then(d => {
    if (d.tunnel_url) {
      navigator.clipboard.writeText(d.tunnel_url);
      alert(`Public Cloudflare SaaS Tunnel URL copied:\n${d.tunnel_url}`);
    }
  });
}

// --------------------------------------------------------------------------
// 7. DUPLEX SPEECH TRANSCEIVER (STT & TTS WAVEFORM)
// --------------------------------------------------------------------------
function initSTT() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    composerMicBtnEl.style.display = "none";
    return;
  }

  STATE.recognition = new SpeechRecognition();
  STATE.recognition.continuous = false;
  STATE.recognition.interimResults = false;
  STATE.recognition.lang = "en-US";

  STATE.recognition.onresult = (e) => {
    const text = e.results[0][0].transcript;
    composerInputEl.value = text;
    dispatchComposer();
  };

  STATE.recognition.onerror = () => {
    stopMic();
  };

  STATE.recognition.onend = () => {
    stopMic();
  };
}

function toggleMic() {
  if (STATE.isRecording) {
    stopMic();
  } else {
    startMic();
  }
}

function startMic() {
  if (!STATE.recognition) return;
  try {
    STATE.recognition.start();
    STATE.isRecording = true;
    composerMicBtnEl.classList.add("recording");
    document.getElementById("micBtn").classList.add("active");
  } catch (err) {}
}

function stopMic() {
  if (STATE.recognition && STATE.isRecording) {
    try { STATE.recognition.stop(); } catch (e) {}
  }
  STATE.isRecording = false;
  composerMicBtnEl.classList.remove("recording");
  document.getElementById("micBtn").classList.remove("active");
}

voiceToggleBtnEl.addEventListener("click", () => {
  STATE.voiceEnabled = !STATE.voiceEnabled;
  voiceToggleBtnEl.classList.toggle("active", STATE.voiceEnabled);
  ctxVoiceStatusEl.textContent = STATE.voiceEnabled ? "DAC Active" : "Muted";
});

function initWaveform() {
  const canvas = document.getElementById("voiceWaveform");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  let t = 0;
  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.lineWidth = 2;
    ctx.strokeStyle = STATE.voiceEnabled ? "#00f0ff" : "#64748b";
    ctx.beginPath();

    const mid = canvas.height / 2;
    const amp = STATE.voiceEnabled ? (STATE.isStreaming ? 14 : 4) : 1;

    for (let x = 0; x < canvas.width; x++) {
      const y = mid + Math.sin(x * 0.05 + t) * Math.cos(x * 0.02 + t * 0.5) * amp;
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
    t += 0.05;
    requestAnimationFrame(draw);
  }
  draw();
}
