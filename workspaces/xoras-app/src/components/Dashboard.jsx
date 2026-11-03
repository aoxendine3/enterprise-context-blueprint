import { useApp } from "../context/AppContext";
import { CLOUD_DAXX_TEAM, ALL_SOVEREIGN_SKILLS } from "../lib/constants";

function MetricCard({ label, value, unit, sub, percent, color = "accent", icon }) {
  const clampedPct = Math.min(100, Math.max(0, percent || 0));
  const colorClass = percent > 85 ? "red" : percent > 65 ? "yellow" : color;

  return (
    <div className="metric-card">
      <div className="metric-label">
        {icon && <span>{icon}</span>}
        {label}
      </div>
      <div className={`metric-value ${colorClass}`}>
        {value}<span style={{ fontSize: 14, fontWeight: 400, color: "var(--text-muted)", marginLeft: 4 }}>{unit}</span>
      </div>
      {percent !== undefined && (
        <div className="metric-bar-track">
          <div className={`metric-bar-fill ${colorClass}`} style={{ width: `${clampedPct}%` }} />
        </div>
      )}
      {sub && <div className="metric-sub">{sub}</div>}
    </div>
  );
}

export default function Dashboard() {
  const { state, dispatch, newConversation, speak, openSkillInFiles } = useApp();
  const { metrics, metricsLoading, dojoErrors, modelStatus, models, conversations } = state;

  const recentErrors = dojoErrors?.slice(0, 4) || [];
  const openErrors = dojoErrors?.filter(e => e.status !== "archived").length || 0;
  const now = new Date();
  const hour = now.getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
  const coreConductors = CLOUD_DAXX_TEAM.slice(0, 8);
  const featuredSkills = ALL_SOVEREIGN_SKILLS.slice(0, 6);

  return (
    <div className="panel-content">
      <div className="dashboard">
        {/* Executive Header & Primary Action Bar */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "var(--s4)", flexWrap: "wrap" }}>
          <div className="dashboard-greeting" style={{ marginBottom: 0 }}>
            <h1>{greeting}, Anthony.</h1>
            <p style={{ color: "var(--text-secondary)" }}>
              {conversations.filter(c => c.status === "in_progress").length} active session
              {conversations.filter(c => c.status === "in_progress").length !== 1 ? "s" : ""} ·{" "}
              {models.length} model{models.length !== 1 ? "s" : ""} ready ·{" "}
              <span style={{ color: modelStatus?.ollama_online ? "var(--green)" : "var(--red)", fontWeight: 500 }}>
                Local Node {modelStatus?.ollama_online ? "Online" : "Offline"}
              </span>
            </p>
          </div>

          <div className="quick-actions">
            <button className="quick-btn primary" onClick={() => { newConversation(); dispatch({ type: "SET_VIEW", payload: "chat" }); }}>
              + New Chat
            </button>
            <button className="quick-btn" onClick={() => dispatch({ type: "SET_VIEW", payload: "daxx_team" })}>
              ☁️ DAXX Nexus
            </button>
            <button className="quick-btn" onClick={() => dispatch({ type: "SET_VIEW", payload: "terminal" })}>
              ⌗ Terminal
            </button>
            <button className="quick-btn" onClick={() => dispatch({ type: "SET_VIEW", payload: "files" })}>
              ⊞ Files
            </button>
            <button className="quick-btn" onClick={() => speak("DAXX here, Master Conductor of the eighty-four helper swarm. Systems nominal.", "am_fenrir", 1.08)}>
              ♪ DAXX Voice Check
            </button>
          </div>
        </div>

        {/* Apple Silicon M4 Hardware Telemetry */}
        <div>
          <div className="section-label" style={{ padding: "0 0 10px" }}>Apple Silicon M4 Hardware Telemetry</div>
          {metrics ? (
            <div className="metrics-grid">
              <MetricCard
                label="CPU Load"
                icon="⬡"
                value={(metrics.cpu_usage ?? 0).toFixed(1)}
                unit="%"
                percent={metrics.cpu_usage ?? 0}
                sub="Unified compute cores"
              />
              <MetricCard
                label="Unified RAM"
                icon="▣"
                value={(metrics.ram_used_gb ?? 0).toFixed(1)}
                unit="GB"
                percent={metrics.ram_percent ?? 0}
                sub={`${(metrics.ram_total_gb ?? 0).toFixed(0)} GB total`}
              />
              <MetricCard
                label="Disk Used"
                icon="◫"
                value={(metrics.disk_used_gb ?? 0).toFixed(0)}
                unit="GB"
                percent={metrics.disk_percent ?? 0}
                sub={`${(metrics.disk_available_gb ?? ((metrics.disk_total_gb ?? 0) - (metrics.disk_used_gb ?? 0))).toFixed(1)} GB available`}
              />
              <MetricCard
                label="Storage Capacity"
                icon="◫"
                value={(metrics.disk_total_gb ?? 0).toFixed(0)}
                unit="GB"
                color="green"
                sub={`${(metrics.disk_percent ?? 0).toFixed(1)}% allocated`}
              />
            </div>
          ) : (
            <div style={{ color: "var(--text-muted)", fontSize: 13, padding: "12px 0" }}>
              {metricsLoading ? "Sampling hardware telemetry…" : "Telemetry initializing…"}
            </div>
          )}
        </div>

        {/* Two-Column Executive Overview */}
        <div className="dashboard-two-col">
          {/* Left Column: Sovereign Conductors & Skills */}
          <div className="section-card">
            <div className="section-card-header">
              <span style={{ color: "var(--accent)", fontSize: 13 }}>☁️</span>
              <span className="section-card-title">Sovereign Conductors &amp; Core Skills</span>
              <span className="tag green">
                {CLOUD_DAXX_TEAM.length} Conductors · {ALL_SOVEREIGN_SKILLS.length} Skills
              </span>
              <button
                className="quick-btn"
                style={{ marginLeft: "auto", padding: "3px 10px", fontSize: 11, color: "var(--accent)", borderColor: "var(--border-accent)" }}
                onClick={() => dispatch({ type: "SET_VIEW", payload: "daxx_team" })}
              >
                All Conductors →
              </button>
            </div>
            <div className="section-card-body" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                {coreConductors.map(member => (
                  <button
                    key={member.id}
                    className="quick-btn"
                    style={{ fontSize: 11.5, padding: "6px 10px", justifyContent: "flex-start" }}
                    onClick={() => dispatch({ type: "SET_VIEW", payload: "daxx_team" })}
                    title={member.role}
                  >
                    <span style={{ color: "var(--accent)", fontWeight: 700, fontFamily: "var(--font-mono)" }}>{member.id}</span>
                    <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {member.name.split("(")[0].trim()}
                    </span>
                  </button>
                ))}
              </div>
              <div style={{ borderTop: "1px solid var(--border)", paddingTop: 10, display: "flex", alignItems: "center", flexWrap: "wrap", gap: 6 }}>
                <span style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 600, marginRight: 4 }}>
                  Pinned Skills:
                </span>
                {featuredSkills.map(skill => (
                  <button
                    key={skill.id}
                    className="quick-btn"
                    style={{ fontSize: 11, padding: "3px 8px", color: "var(--green)" }}
                    onClick={() => openSkillInFiles(skill.path)}
                    title={`Open ${skill.path}`}
                  >
                    ↗ {skill.name}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column: Active Models & Omni-Dojo Status */}
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--s5)" }}>
            <div className="section-card">
              <div className="section-card-header">
                <span style={{ color: "var(--accent)", fontSize: 13 }}>◈</span>
                <span className="section-card-title">Inference Engines</span>
                <span className="tag green" style={{ marginLeft: "auto" }}>
                  {models.length} ready
                </span>
              </div>
              <div className="section-card-body">
                {models.length === 0 ? (
                  <div style={{ fontSize: 13, color: "var(--text-muted)", padding: "8px 0" }}>
                    Probing model endpoints…
                  </div>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column" }}>
                    {models.slice(0, 5).map(m => (
                      <div key={m.id} className="model-row">
                        <span className={`model-provider ${m.provider}`}>{m.provider}</span>
                        <span className="model-name">{m.name}</span>
                        {m.size && <span className="model-size" style={{ marginLeft: "auto" }}>{m.size}</span>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="section-card">
              <div className="section-card-header">
                <span style={{ color: "var(--accent-2)", fontSize: 13 }}>◈</span>
                <span className="section-card-title">Omni-Dojo Watchdog</span>
                {openErrors > 0 && <span className="tag red" style={{ marginLeft: "auto" }}>{openErrors} open</span>}
                <button
                  className="quick-btn"
                  style={{ marginLeft: openErrors > 0 ? 8 : "auto", padding: "3px 10px", fontSize: 11 }}
                  onClick={() => dispatch({ type: "SET_VIEW", payload: "dojo" })}
                >
                  Open Dojo →
                </button>
              </div>
              <div className="section-card-body">
                {recentErrors.length === 0 ? (
                  <div style={{ fontSize: 13, color: "var(--green)", padding: "6px 0" }}>
                    ✓ Zero unresolved anomalies in Catalyst ledger
                  </div>
                ) : (
                  recentErrors.map(err => (
                    <div key={err.id} className="error-row">
                      <div className="error-header">
                        <span className={`error-badge ${err.status === "archived" ? "archived" : "open"}`}>
                          {err.status}
                        </span>
                        <span className="error-type">{err.exception_type}</span>
                        <span className="error-time">{err.timestamp?.slice(0, 16) || ""}</span>
                      </div>
                      <div className="error-msg">{err.error_message?.slice(0, 100)}{err.error_message?.length > 100 ? "…" : ""}</div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
