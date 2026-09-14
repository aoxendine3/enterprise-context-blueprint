/**
 * XMARS.os Sovereign Neural Client Application
 * Full Duplex STS (Speech-to-Speech), STT Microphone Intake,
 * Agent TTS Synthesizer, 60fps Oscilloscope HUD, and Internal Rails.
 */

const STATE = {
  currentAgent: "maxx",
  currentModel: "sovereign-hermes:latest",
  agents: {},
  models: [],
  isStreaming: false,
  health: {},
  voiceEnabled: true,
  stsContinuous: false,
  isListening: false,
  recognition: null,
  silenceTimer: null
};

// DOM Cache
const councilListEl = document.getElementById("councilList");
const modelSelectEl = document.getElementById("modelSelect");
const chatStreamEl = document.getElementById("chatStream");
const chatInputEl = document.getElementById("chatInput");
const sendBtnEl = document.getElementById("sendBtn");
const micBtnEl = document.getElementById("micBtn");
const voiceToggleBtnEl = document.getElementById("voiceToggleBtn");
const stsToggleBtnEl = document.getElementById("stsToggleBtn");
const healthPillEl = document.getElementById("healthPill");
const latencyLabelEl = document.getElementById("latencyLabel");
const inspectorEl = document.getElementById("xmarsInspector");
const inspectorTitleEl = document.getElementById("inspectorTitle");
const inspectorContentEl = document.getElementById("inspectorContent");

// Voice Mapping for Sovereign Council Personas
const AGENT_VOICE_PROFILES = {
  maxx: { pitch: 0.95, rate: 1.05, voiceLang: "en-US" },
  jarvis: { pitch: 1.0, rate: 1.0, voiceLang: "en-US" },
  clara: { pitch: 1.15, rate: 1.05, voiceLang: "en-US" },
  vance: { pitch: 0.85, rate: 1.1, voiceLang: "en-US" },
  daxx: { pitch: 0.9, rate: 1.15, voiceLang: "en-US" },
  orion: { pitch: 1.05, rate: 1.0, voiceLang: "en-US" }
};

// Initialize XMARS.os Client
async function initXmars() {
  await loadCouncil();
  await loadModels();
  await refreshHealth();
  setInterval(refreshHealth, 8000);

  initSTT();

  chatInputEl.addEventListener("input", autoResizeInput);
  chatInputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      dispatchMessage();
    }
  });

  sendBtnEl.addEventListener("click", () => dispatchMessage());
  micBtnEl.addEventListener("click", toggleMic);
  voiceToggleBtnEl.addEventListener("click", toggleVoiceOutput);
  stsToggleBtnEl.addEventListener("click", toggleSTSMode);

  initOscilloscope();
}

function autoResizeInput() {
  chatInputEl.style.height = "auto";
  chatInputEl.style.height = Math.min(chatInputEl.scrollHeight, 180) + "px";
}

// Load Sovereign Council
async function loadCouncil() {
  try {
    const res = await fetch("/api/agents");
    const data = await res.json();
    if (data.status === "success") {
      STATE.agents = data.agents;
      renderCouncil();
    }
  } catch (err) {
    console.error("Failed to load council:", err);
  }
}

function renderCouncil() {
  councilListEl.innerHTML = "";
  Object.values(STATE.agents).forEach(agent => {
    const card = document.createElement("div");
    card.className = `council-card ${agent.id === STATE.currentAgent ? "selected" : ""}`;
    card.onclick = () => selectAgent(agent.id);

    card.innerHTML = `
      <div class="card-avatar" style="background: ${agent.color};">
        ${agent.avatar}
      </div>
      <div class="card-info">
        <div class="card-name">${agent.name}</div>
        <div class="card-role">${agent.title}</div>
      </div>
    `;
    councilListEl.appendChild(card);
  });
}

function selectAgent(id) {
  STATE.currentAgent = id;
  renderCouncil();
  const agent = STATE.agents[id];
  if (agent) {
    appendNotice(`Engaged Sovereign Agent: <strong style="color:${agent.color};">${agent.name}</strong> (${agent.role})`);
    if (STATE.voiceEnabled) {
      speakText(`Sovereign agent ${agent.name} online.`);
    }
  }
}

// Load Models
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
  appendNotice(`Active Neural Engine set to <code>${STATE.currentModel}</code>`);
});

// Telemetry & Health
async function refreshHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    STATE.health = data;
    if (data.inference_engine_online) {
      healthPillEl.style.borderColor = "#059669";
      healthPillEl.style.background = "#064e3b";
      healthPillEl.style.color = "#6ee7b7";
      latencyLabelEl.textContent = `Online • ${data.engine_latency_ms}ms • ${data.active_model}`;
    } else {
      healthPillEl.style.borderColor = "#dc2626";
      healthPillEl.style.background = "#7f1d1d";
      healthPillEl.style.color = "#fca5a5";
      latencyLabelEl.textContent = `Autonomous Core Active (XTC-v1)`;
    }
  } catch (err) {
    latencyLabelEl.textContent = `Host Disconnected`;
  }
}

// Speech-To-Text (STT) Engine
function initSTT() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) {
    micBtnEl.title = "STT not supported in this browser";
    micBtnEl.style.opacity = "0.5";
    return;
  }

  STATE.recognition = new SpeechRec();
  STATE.recognition.continuous = true;
  STATE.recognition.interimResults = true;
  STATE.recognition.lang = "en-US";

  STATE.recognition.onstart = () => {
    STATE.isListening = true;
    micBtnEl.classList.add("listening");
    micBtnEl.title = "Listening... Click to stop";
  };

  STATE.recognition.onresult = (event) => {
    let transcript = "";
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      transcript += event.results[i][0].transcript;
    }
    chatInputEl.value = transcript;
    autoResizeInput();

    // Auto-dispatch in continuous STS mode if user pauses for 1.3 seconds
    if (STATE.stsContinuous) {
      clearTimeout(STATE.silenceTimer);
      STATE.silenceTimer = setTimeout(() => {
        if (chatInputEl.value.trim().length > 0) {
          logSTTReceipt(chatInputEl.value.trim());
          stopListening();
          dispatchMessage();
        }
      }, 1300);
    }
  };

  function logSTTReceipt(text) {
    try {
      fetch("/api/stt/event", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript: text, agent: STATE.currentAgent })
      });
    } catch (e) {}
  }

  STATE.recognition.onerror = (err) => {
    console.warn("STT Error:", err);
    stopListening();
  };

  STATE.recognition.onend = () => {
    STATE.isListening = false;
    micBtnEl.classList.remove("listening");
    micBtnEl.title = "Voice Input (Click to speak)";
  };
}

function toggleMic() {
  if (STATE.isListening) {
    stopListening();
  } else {
    startListening();
  }
}

function startListening() {
  if (STATE.recognition && !STATE.isListening) {
    try {
      STATE.recognition.start();
    } catch (e) {}
  }
}

function stopListening() {
  if (STATE.recognition && STATE.isListening) {
    try {
      STATE.recognition.stop();
    } catch (e) {}
  }
}

// Text-To-Speech (TTS) Engine
function speakText(text) {
  if (!STATE.voiceEnabled || !window.speechSynthesis) return;

  window.speechSynthesis.cancel(); // Flush queue to prevent overlapping output
  const profile = AGENT_VOICE_PROFILES[STATE.currentAgent] || { pitch: 1.0, rate: 1.0 };
  
  // Clean markdown tokens before speaking
  const cleanSpeech = text
    .replace(/```[\s\S]*?```/g, "Code block omitted.")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/[#*_~>]/g, "")
    .replace(/\n+/g, " ")
    .trim();

  if (!cleanSpeech) return;

  const utterance = new SpeechSynthesisUtterance(cleanSpeech);
  utterance.pitch = profile.pitch;
  utterance.rate = profile.rate;
  utterance.lang = profile.voiceLang;

  // Re-arm listening if in continuous STS mode
  utterance.onend = () => {
    if (STATE.stsContinuous && !STATE.isStreaming) {
      setTimeout(() => startListening(), 400);
    }
  };

  window.speechSynthesis.speak(utterance);
}

function toggleVoiceOutput() {
  STATE.voiceEnabled = !STATE.voiceEnabled;
  voiceToggleBtnEl.classList.toggle("active", STATE.voiceEnabled);
  voiceToggleBtnEl.textContent = STATE.voiceEnabled ? "🔊 Voice: ON" : "🔇 Voice: OFF";
  if (!STATE.voiceEnabled && window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
}

function toggleSTSMode() {
  STATE.stsContinuous = !STATE.stsContinuous;
  stsToggleBtnEl.classList.toggle("active", STATE.stsContinuous);
  stsToggleBtnEl.textContent = STATE.stsContinuous ? "🎙️ Hands-Free STS: ACTIVE" : "🎙️ STS Mode";
  if (STATE.stsContinuous) {
    STATE.voiceEnabled = true;
    voiceToggleBtnEl.classList.add("active");
    voiceToggleBtnEl.textContent = "🔊 Voice: ON";
    appendNotice("<strong>Hands-Free Speech-to-Speech (STS) Engaged.</strong> Speak freely; agents respond and re-arm microphone automatically.");
    startListening();
  } else {
    stopListening();
  }
}

// Message Dispatch & SSE Streaming
async function dispatchMessage() {
  const text = chatInputEl.value.trim();
  if (!text || STATE.isStreaming) return;

  if (text.startsWith("/")) {
    chatInputEl.value = "";
    autoResizeInput();
    runAcceleratorCommand(text);
    return;
  }

  appendMessage("user", "Anthony", text, null);
  chatInputEl.value = "";
  autoResizeInput();

  STATE.isStreaming = true;
  sendBtnEl.disabled = true;

  const agent = STATE.agents[STATE.currentAgent] || { name: "Maxx", color: "#06b6d4" };
  const bubble = createStreamBubble(agent);
  chatStreamEl.appendChild(bubble.row);
  chatStreamEl.scrollTop = chatStreamEl.scrollHeight;

  let accumulated = "";

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
            accumulated += payload.token;
            bubble.contentEl.innerHTML = formatMarkdown(accumulated);
            chatStreamEl.scrollTop = chatStreamEl.scrollHeight;
          }
          if (payload.done) {
            bubble.telemetryEl.textContent = `${payload.ttft_sec}s TTFT • ${payload.tokens_per_sec} tok/s • ${payload.token_count} tokens`;
            speakText(accumulated);
            break;
          }
        } catch (e) {}
      }
    }
  } catch (err) {
    bubble.contentEl.innerHTML += `<div style="color: #ef4444;">[XMARS Engine Error: ${err.message}]</div>`;
  } finally {
    STATE.isStreaming = false;
    sendBtnEl.disabled = false;
  }
}

// Accelerator Execution
async function runAcceleratorCommand(cmd) {
  const parts = cmd.split(" ");
  const toolName = parts[0].replace("/", "").toLowerCase();
  const rest = parts.slice(1).join(" ");

  appendNotice(`⚡ Executing Accelerator: <code>/${toolName}</code>`);

  try {
    let payload = { tool: toolName, params: {} };
    if (toolName === "distill") {
      payload.params = { text: rest || "XMARS.os sovereign intelligence eliminates external data leakage." };
    } else if (toolName === "drift") {
      payload.params = { target_dir: "." };
    } else if (toolName === "audit") {
      payload.params = {};
    } else if (toolName === "speak") {
      payload.params = { agent: STATE.currentAgent, message: rest || "XMARS dot os physical transceiver clear." };
    } else if (toolName === "heal") {
      const res = await fetch("/api/remediate", { method: "POST" });
      const data = await res.json();
      showInspector("Autonomous Remediation Output", data);
      return;
    }

    const res = await fetch("/api/tools/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    showInspector(`Accelerator: /${toolName}`, result);
  } catch (err) {
    appendNotice(`❌ Accelerator failed: ${err.message}`);
  }
}

function showInspector(title, data) {
  inspectorTitleEl.textContent = title;
  inspectorContentEl.textContent = JSON.stringify(data, null, 2);
  inspectorEl.classList.remove("hidden");
}

function toggleInspector() {
  inspectorEl.classList.toggle("hidden");
}

function triggerPill(cmd) {
  chatInputEl.value = cmd + " ";
  chatInputEl.focus();
  autoResizeInput();
}

// UI Formatting
function appendMessage(role, senderName, text, telemetry) {
  const row = document.createElement("div");
  row.className = `msg-row ${role}`;
  row.innerHTML = `
    <div class="msg-bubble">
      <div class="msg-header">
        <div class="msg-sender">${senderName}</div>
        ${telemetry ? `<div class="msg-telemetry">${telemetry}</div>` : ""}
      </div>
      <div class="msg-text">${formatMarkdown(text)}</div>
    </div>
  `;
  chatStreamEl.appendChild(row);
  chatStreamEl.scrollTop = chatStreamEl.scrollHeight;
}

function createStreamBubble(agent) {
  const row = document.createElement("div");
  row.className = "msg-row assistant";
  row.innerHTML = `
    <div class="msg-bubble">
      <div class="msg-header">
        <div class="msg-sender" style="color: ${agent.color};">
          <span style="display:inline-block; width:8px; height:8px; background:${agent.color}; border-radius:50%;"></span>
          ${agent.name}
        </div>
        <div class="msg-telemetry" id="streamTelemetry">Streaming tokens...</div>
      </div>
      <div class="msg-text" id="streamBody"></div>
    </div>
  `;
  return {
    row: row,
    contentEl: row.querySelector("#streamBody"),
    telemetryEl: row.querySelector("#streamTelemetry")
  };
}

function appendNotice(html) {
  const row = document.createElement("div");
  row.style.textAlign = "center";
  row.style.fontSize = "12px";
  row.style.color = "#9ca3af";
  row.style.margin = "8px 0";
  row.innerHTML = `<span>${html}</span>`;
  chatStreamEl.appendChild(row);
  chatStreamEl.scrollTop = chatStreamEl.scrollHeight;
}

function formatMarkdown(src) {
  if (!src) return "";
  let out = src.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  out = out.replace(/```(\w+)?\n([\s\S]*?)```/g, (m, l, code) => {
    return `<pre><code>${code.trim()}</code><button class="code-copy-btn" onclick="copySnippet(this)">Copy</button></pre>`;
  });
  out = out.replace(/`([^`]+)`/g, '<code style="background:#1f2937; padding:2px 6px; border-radius:4px; font-family:var(--font-code); color:#38bdf8;">$1</code>');
  out = out.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  out = out.replace(/\n/g, '<br/>');
  return out;
}

function copySnippet(btn) {
  const code = btn.parentElement.querySelector("code");
  if (code) {
    navigator.clipboard.writeText(code.innerText);
    btn.textContent = "Copied!";
    setTimeout(() => { btn.textContent = "Copy"; }, 2000);
  }
}

// 60fps Oscilloscope Canvas
function initOscilloscope() {
  const canvas = document.createElement("canvas");
  canvas.style.position = "absolute";
  canvas.style.bottom = "84px";
  canvas.style.right = "24px";
  canvas.style.width = "220px";
  canvas.style.height = "55px";
  canvas.style.pointerEvents = "none";
  canvas.style.opacity = "0.8";
  canvas.style.zIndex = "15";
  document.querySelector(".xmars-main").appendChild(canvas);

  const ctx = canvas.getContext("2d");
  let step = 0;

  function loop() {
    canvas.width = 220;
    canvas.height = 55;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const active = STATE.isStreaming || STATE.isListening;
    const amp = STATE.isListening ? 18 : (STATE.isStreaming ? 14 : 3);
    const speed = active ? 0.16 : 0.04;
    step += speed;

    ctx.beginPath();
    ctx.lineWidth = 2;
    ctx.strokeStyle = STATE.isListening ? "#ef4444" : (STATE.isStreaming ? "#06b6d4" : "#374151");
    ctx.shadowBlur = active ? 10 : 0;
    ctx.shadowColor = STATE.isListening ? "#ef4444" : "#06b6d4";

    for (let x = 0; x < canvas.width; x++) {
      const y = canvas.height / 2 + Math.sin(x * 0.04 + step) * amp * Math.cos(x * 0.015 + step * 0.5);
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    requestAnimationFrame(loop);
  }
  loop();
}

window.addEventListener("DOMContentLoaded", initXmars);
