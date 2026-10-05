import { useState } from 'react'
import {
  BarChart3, BrainCircuit, ChevronLeft, ChevronRight,
  FileText, LogOut, PieChart, Settings, Shield, Upload, Users, ShieldAlert,
} from 'lucide-react'

const NAV_ITEMS = [
  { key: 'dashboard',   label: 'Dashboard',             Icon: BarChart3 },
  { key: 'upload',      label: 'Dataset Upload',         Icon: Upload },
  { key: 'predict',     label: 'Churn Prediction',       Icon: BrainCircuit },
  { key: 'risk',        label: 'Risk Analysis',          Icon: Users },
  { key: 'performance', label: 'Model Performance',      Icon: PieChart },
  { key: 'retention',   label: 'Retention Strategy',     Icon: Shield },
  { key: 'reviews',     label: 'Safety Reviews',         Icon: ShieldAlert },
  { key: 'reports',     label: 'Reports',                Icon: FileText },
  { key: 'settings',    label: 'Settings',               Icon: Settings },
]

export default function Sidebar({ page, setPage, logout }) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside
      className={`hidden lg:flex shrink-0 h-screen sticky top-0 overflow-hidden glass border-r border-white/10 flex-col transition-all duration-300 ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Logo */}
      <div className={`flex items-center gap-3 p-4 mb-4 border-b border-white/10 ${collapsed ? 'justify-center' : ''}`}>
        <div className="w-10 h-10 rounded-xl glow-btn flex items-center justify-center shrink-0">
          <Shield size={20} />
        </div>
        {!collapsed && (
          <div className="overflow-hidden">
            <h2 className="font-bold text-sm leading-tight">ChurnShield AI</h2>
            <p className="text-xs text-slate-400 truncate">XGBoost Intelligence</p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 min-h-0 space-y-1 px-2 overflow-hidden">
        {NAV_ITEMS.map(({ key, label, Icon }) => (
          <button
            key={key}
            onClick={() => setPage(key)}
            title={collapsed ? label : undefined}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-left transition-all ${
              page === key ? 'nav-active' : 'text-slate-300 hover:bg-white/5'
            } ${collapsed ? 'justify-center' : ''}`}
          >
            <Icon size={18} className="shrink-0" />
            {!collapsed && <span className="truncate">{label}</span>}
          </button>
        ))}
      </nav>

      {/* Bottom actions */}
      <div className="p-2 border-t border-white/10 space-y-1">
        <button
          onClick={() => setCollapsed((c) => !c)}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-slate-400 hover:bg-white/5"
          title={collapsed ? 'Expand' : 'Collapse'}
        >
          {collapsed ? <ChevronRight size={18} /> : <><ChevronLeft size={18} /><span>Collapse</span></>}
        </button>
        <button
          onClick={logout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-red-300 hover:bg-red-500/10"
        >
          <LogOut size={18} className="shrink-0" />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </aside>
  )
}
