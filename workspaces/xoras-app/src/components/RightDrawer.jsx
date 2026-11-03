import { useState } from "react";
import { useApp } from "../context/AppContext";
import {
  CLOUD_DAXX_TEAM,
  PINNED_KNOWLEDGE_RESOURCES,
} from "../lib/constants";

export default function RightDrawer() {
  const {
    state,
    dispatch,
    openSkillInFiles,
    runTerminalCommand,
  } = useApp();
  const {
    rightDrawerOpen,
    rightDrawerTab,
    models,
    selectedModel,
    modelStatus,
    metrics,
  } = state;
  const [quickCmd, setQuickCmd] = useState("");
  const [quickOut, setQuickOut] = useState("");
  const [runningCmd, setRunningCmd] = useState(false);

  const setTab = (t) => dispatch({ type: "SET_RIGHT_DRAWER_TAB", payload: t });
  const toggleDrawer = () => dispatch({ type: "TOGGLE_RIGHT_DRAWER" });

  const handleQuickRun = async () => {
    const cmd = quickCmd.trim();
    if (!cmd || runningCmd) return;
    setRunningCmd(true);
    setQuickOut(`$ ${cmd}\nRunning…`);
    try {
      await runTerminalCommand(cmd);
      setQuickOut(`✓ Dispatched '${cmd}' to Xoras Terminal.`);
      setQuickCmd("");
    } catch (e) {
      setQuickOut(`✗ ${String(e)}`);
    } finally {
      setRunningCmd(false);
    }
  };

  if (!rightDrawerOpen) {
    return null;
  }

  return (
    <aside className="right-drawer open">
        <div className="right-drawer-header">
          <div className="right-drawer-tabs">
            {[
              { id: "agents",    label: "Agents (21)" },
              { id: "knowledge", label: "SSOT (10)" },
              { id: "nodes",     label: "Nodes & Term" },
            ].map(t => (
              <button
                key={t.id}
                type="button"
                className={`right-drawer-tab ${rightDrawerTab === t.id ? "active" : ""}`}
                onClick={() => setTab(t.id)}
              >
                {t.label}
              </button>
            ))}
          </div>
          <button
            type="button"
            className="drawer-close-btn"
            onClick={toggleDrawer}
            title="Collapse Right Drawer"
          >
            ✕
          </button>
        </div>

        <div className="right-drawer-body">
          {/* TAB 1: 21 AGENTS QUICK DISPATCH */}
          {rightDrawerTab === "agents" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 2 }}>
                Click any agent to open in Chat or inspect in the Collective Nexus:
              </div>
              {CLOUD_DAXX_TEAM.map(agent => {
                const handle = agent.mention || agent.id.toLowerCase().replace("-", "");
                return (
                  <div key={agent.id} className="drawer-card">
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 6 }}>
                      <span style={{ fontSize: 11, fontWeight: 700, color: "var(--accent)", fontFamily: "var(--font-mono)" }}>
                        @{handle}
                      </span>
                      <span className="tag green" style={{ fontSize: 9, padding: "1px 6px" }}>
                        {agent.badge}
                      </span>
                    </div>
                    <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-primary)" }}>
                      {agent.name}
                    </div>
                    <div style={{ fontSize: 11, color: "var(--text-secondary)", lineHeight: 1.35 }}>
                      {agent.role}
                    </div>
                    <div style={{ display: "flex", gap: 6, marginTop: 4 }}>
                      <button
                        type="button"
                        className="quick-btn"
                        style={{ flex: 1, fontSize: 10.5, padding: "3px 6px", justifyContent: "center", color: "var(--accent)" }}
                        onClick={() => {
                          dispatch({ type: "SET_VIEW", payload: "chat" });
                          dispatch({ type: "SET_DRAFT_PROMPT", payload: `@${handle} ` });
                        }}
                      >
                        ⚡ @Mention in Chat
                      </button>
                      <button
                        type="button"
                        className="quick-btn"
                        style={{ fontSize: 10.5, padding: "3px 8px" }}
                        onClick={() => openSkillInFiles(agent.scriptPath)}
                        title="Open Runner Script"
                      >
                        ↗ Script
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* TAB 2: 10 PINNED SSOT KNOWLEDGE DOCS */}
          {rightDrawerTab === "knowledge" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 2 }}>
                10 SHA-256 Pinned Local SSOT Knowledge Docs (0ms Local Read):
              </div>
              {PINNED_KNOWLEDGE_RESOURCES.map(kr => (
                <div key={kr.id} className="drawer-card">
                  <div style={{ fontSize: 11.5, fontWeight: 600, color: "var(--text-primary)", wordBreak: "break-word" }}>
                    {kr.fileName}
                  </div>
                  <div style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--green)" }}>
                    SHA-256: {kr.sha256}… · {(kr.sizeBytes / 1024).toFixed(1)} KB
                  </div>
                  <div style={{ display: "flex", gap: 6, marginTop: 4 }}>
                    <button
                      type="button"
                      className="quick-btn"
                      style={{ flex: 1, fontSize: 10.5, padding: "3px 8px", justifyContent: "center", color: "var(--accent)" }}
                      onClick={() => openSkillInFiles(kr.localPath)}
                    >
                      ↗ Open in File Editor
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* TAB 3: NODES, MODELS & QUICK TERMINAL */}
          {rightDrawerTab === "nodes" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <div className="drawer-card">
                <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>
                  Active Inference Nodes
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 4 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
                    <span>M4 Local (127.0.0.1)</span>
                    <span style={{ color: modelStatus?.ollama_online ? "var(--green)" : "var(--red)", fontWeight: 600 }}>
                      {modelStatus?.ollama_online ? `● ${modelStatus?.ollama_count || 0} models` : "○ Offline"}
                    </span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
                    <span>Windows LAN (192.168.1.211)</span>
                    <span style={{ color: modelStatus?.windows_online ? "var(--green)" : "var(--red)", fontWeight: 600 }}>
                      {modelStatus?.windows_online ? `● ${modelStatus?.windows_count || 0} models` : "○ Offline"}
                    </span>
                  </div>
                </div>
              </div>

              <div className="drawer-card">
                <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>
                  Quick Model Switch ({models?.length || 0})
                </div>
                <select
                  className="field-input field-input-mono"
                  style={{ fontSize: 11.5, padding: "6px 8px", marginTop: 4 }}
                  value={selectedModel}
                  onChange={e => dispatch({ type: "SET_SELECTED_MODEL", payload: e.target.value })}
                >
                  {(models || []).map(m => (
                    <option key={m.id} value={m.id}>
                      [{m.badge}] {m.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="drawer-card">
                <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>
                  Quick Command Dispatch
                </div>
                <div style={{ display: "flex", gap: 6, marginTop: 4 }}>
                  <input
                    className="field-input field-input-mono"
                    style={{ flex: 1, fontSize: 11.5, padding: "5px 8px" }}
                    placeholder="e.g. pytest -q"
                    value={quickCmd}
                    onChange={e => setQuickCmd(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && handleQuickRun()}
                  />
                  <button
                    type="button"
                    className="save-btn"
                    style={{ padding: "5px 10px", fontSize: 11 }}
                    onClick={handleQuickRun}
                  >
                    Run
                  </button>
                </div>
                {quickOut && (
                  <div style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--green)", marginTop: 4 }}>
                    {quickOut}
                  </div>
                )}
              </div>

              {metrics && (
                <div className="drawer-card">
                  <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>
                    Live Apple Silicon M4 Telemetry
                  </div>
                  <div style={{ fontSize: 12, fontFamily: "var(--font-mono)", display: "flex", flexDirection: "column", gap: 4, marginTop: 4 }}>
                    <div>CPU Load: <span style={{ color: "var(--accent)" }}>{(metrics.cpu_usage ?? 0).toFixed(1)}%</span></div>
                    <div>Unified RAM: <span style={{ color: "var(--green)" }}>{(metrics.ram_used_gb ?? 0).toFixed(1)} / {(metrics.ram_total_gb ?? 0).toFixed(0)} GB</span></div>
                    <div>Disk Free: <span style={{ color: "var(--text-primary)" }}>{(metrics.disk_available_gb ?? ((metrics.disk_total_gb ?? 0) - (metrics.disk_used_gb ?? 0))).toFixed(1)} GB</span></div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </aside>
  );
}
