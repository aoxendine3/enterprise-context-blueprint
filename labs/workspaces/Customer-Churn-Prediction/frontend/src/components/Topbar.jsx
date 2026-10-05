import { useState } from 'react'
import { Bell, Menu, Search, Shield, X } from 'lucide-react'

const NAV_ITEMS = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'upload', label: 'Dataset Upload' },
  { key: 'predict', label: 'Churn Prediction' },
  { key: 'risk', label: 'Risk Analysis' },
  { key: 'performance', label: 'Model Performance' },
  { key: 'retention', label: 'Retention Strategy' },
  { key: 'reviews', label: 'Safety Reviews' },
  { key: 'reports', label: 'Reports' },
  { key: 'settings', label: 'Settings' },
]

export default function Topbar({ title, page, setPage, logout }) {
  const [menuOpen, setMenuOpen] = useState(false)
  const [showNotifications, setShowNotifications] = useState(false)
  const [showProfileMenu, setShowProfileMenu] = useState(false)

  return (
    <>
      <header className="h-16 glass border-b border-white/10 flex items-center justify-between px-5 lg:px-8 sticky top-0 z-40">
        {/* Mobile menu button */}
        <button
          className="lg:hidden mr-3 text-slate-300"
          onClick={() => setMenuOpen(true)}
        >
          <Menu size={22} />
        </button>

        {/* Title */}
        <div className="flex-1 min-w-0">
          <h1 className="font-bold text-lg truncate">{title}</h1>
          <p className="text-xs text-slate-400 hidden sm:block">Home / {title}</p>
        </div>

        {/* Right section */}
        <div className="flex items-center gap-3 ml-4">
          <div className="hidden md:flex items-center gap-2 bg-slate-950/60 border border-white/10 rounded-xl px-3 py-2 w-64">
            <Search size={14} className="text-slate-500 shrink-0" />
            <input
              className="bg-transparent outline-none text-sm w-full placeholder-slate-500"
              placeholder="Search..."
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  setPage('predict');
                }
              }}
            />
          </div>

          {/* Notifications Dropdown */}
          <div className="relative">
            <button
              onClick={() => {
                setShowNotifications(!showNotifications)
                setShowProfileMenu(false)
              }}
              className="relative p-2 text-slate-300 hover:text-white rounded-lg hover:bg-white/5 transition"
            >
              <Bell size={18} />
              <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-red-500 animate-ping" />
              <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-red-500" />
            </button>
            {showNotifications && (
              <div className="absolute right-0 mt-2 w-72 glass border border-white/10 rounded-xl p-3 shadow-xl z-50">
                <h4 className="font-bold text-xs text-slate-400 uppercase tracking-wider mb-2 font-mono">Notifications</h4>
                <div className="space-y-2">
                  <div className="p-2 hover:bg-white/5 rounded-lg text-xs transition">
                    <p className="font-semibold text-white">System Shield Active</p>
                    <p className="text-slate-400 mt-0.5 font-mono">Sovereign safety ledger is synced and running.</p>
                  </div>
                  <div className="p-2 hover:bg-white/5 rounded-lg text-xs transition">
                    <p className="font-semibold text-white">XGBoost Model Verified</p>
                    <p className="text-slate-400 mt-0.5 font-mono">Model evaluated at 93.0% accuracy.</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Profile Dropdown */}
          <div className="relative">
            <div
              onClick={() => {
                setShowProfileMenu(!showProfileMenu)
                setShowNotifications(false)
              }}
              className="flex items-center gap-2 cursor-pointer hover:bg-white/5 p-1 rounded-xl transition"
            >
              <div className="w-9 h-9 rounded-full glow-btn flex items-center justify-center shrink-0">
                <Shield size={16} />
              </div>
              <div className="hidden sm:block">
                <p className="text-sm font-semibold leading-tight">Admin</p>
                <p className="text-xs text-slate-400">Administrator</p>
              </div>
            </div>
            {showProfileMenu && (
              <div className="absolute right-0 mt-2 w-48 glass border border-white/10 rounded-xl p-2 shadow-xl z-50">
                <button
                  onClick={() => {
                    setPage('settings')
                    setShowProfileMenu(false)
                  }}
                  className="w-full text-left px-3 py-2 text-xs font-semibold text-slate-300 hover:text-white hover:bg-white/5 rounded-lg transition"
                >
                  Settings
                </button>
                <button
                  onClick={() => {
                    logout()
                    setShowProfileMenu(false)
                  }}
                  className="w-full text-left px-3 py-2 text-xs font-semibold text-red-400 hover:bg-red-500/10 rounded-lg transition"
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Mobile drawer */}
      {menuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/60" onClick={() => setMenuOpen(false)} />
          <aside className="absolute left-0 top-0 bottom-0 w-64 glass border-r border-white/10 flex flex-col p-4">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl glow-btn flex items-center justify-center">
                  <Shield size={18} />
                </div>
                <span className="font-bold">ChurnShield AI</span>
              </div>
              <button onClick={() => setMenuOpen(false)} className="text-slate-400">
                <X size={20} />
              </button>
            </div>
            <nav className="flex-1 space-y-1">
              {NAV_ITEMS.map(({ key, label }) => (
                <button
                  key={key}
                  onClick={() => { setPage(key); setMenuOpen(false) }}
                  className={`w-full text-left px-3 py-2.5 rounded-xl text-sm ${
                    page === key ? 'nav-active' : 'text-slate-300 hover:bg-white/5'
                  }`}
                >
                  {label}
                </button>
              ))}
            </nav>
            <button
              onClick={() => { logout(); setMenuOpen(false) }}
              className="mt-4 text-red-300 text-sm px-3 py-2.5 hover:bg-red-500/10 rounded-xl text-left"
            >
              Logout
            </button>
          </aside>
        </div>
      )}
    </>
  )
}
