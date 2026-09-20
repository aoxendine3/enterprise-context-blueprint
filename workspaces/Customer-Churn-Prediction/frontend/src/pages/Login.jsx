import { useState } from 'react'
import { Eye, EyeOff, Loader2, ShieldCheck } from 'lucide-react'
import { authApi } from '../services/api.js'

const ROLES = ['Admin', 'Data Analyst']

export default function Login({ onSuccess, onBack }) {
  const [form, setForm] = useState({
    email: '',
    password: '',
    role: 'Admin',
  })
  const [showPwd, setShowPwd] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    if (!form.email || !form.password) {
      setError('Please enter your email and password.')
      return
    }
    setError('')
    setLoading(true)
    try {
      const res = await authApi.login(form)
      const token = res.data.token
      localStorage.setItem('churn_token', token)
      localStorage.setItem('churn_user', JSON.stringify(res.data.user || { email: form.email, role: form.role }))
      onSuccess()
    } catch (err) {
      setError(err.response?.data?.message || 'Login failed. Please check MongoDB API connection and credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="ai-bg min-h-screen grid lg:grid-cols-2">
      {/* Left panel */}
      <div className="hidden lg:flex flex-col items-center justify-center relative p-12 gap-8">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-900/20 to-cyan-900/10" />
        <div className="relative w-64 h-64 rounded-full border border-indigo-400/30 flex items-center justify-center">
          <div className="absolute inset-4 rounded-full border border-indigo-400/15" />
          <ShieldCheck size={120} className="text-indigo-300" />
        </div>

        <div className="relative glass p-6 rounded-2xl max-w-sm">
          <h3 className="font-bold text-xl mb-3">AI-Powered Churn Prediction</h3>
          <p className="text-slate-400 text-sm leading-relaxed">
            Leverage XGBoost machine learning to predict customer churn with 94.2% accuracy and protect your revenue.
          </p>
          <div className="grid grid-cols-2 gap-4 mt-6">
            {[['94.2%', 'Accuracy'], ['25.4K+', 'Customers'], ['18.01%', 'Churn Risk'], ['$845K', 'At Risk']].map(([v, l]) => (
              <div key={l} className="text-center">
                <div className="text-cyan-300 font-bold text-xl">{v}</div>
                <div className="text-slate-400 text-xs mt-1">{l}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right panel — form */}
      <div className="flex items-center justify-center p-6">
        <div className="glass rounded-3xl p-8 w-full max-w-md card-3d">
          <button
            type="button"
            onClick={onBack}
            className="text-sm text-slate-400 hover:text-white mb-6 transition-colors"
          >
            ← Back to Home
          </button>

          <div
            onClick={onBack}
            className="flex items-center gap-3 mb-6 cursor-pointer"
          >
            <div className="w-10 h-10 rounded-xl glow-btn flex items-center justify-center">
              <ShieldCheck size={20} />
            </div>
            <h2 className="text-xl font-bold">ChurnShield AI</h2>
          </div>

          <h1 className="text-2xl font-bold">Welcome Back!</h1>
          <p className="text-sm text-slate-400 mb-6 mt-1">Sign in to access your dashboard</p>

          <form onSubmit={submit} className="space-y-4">
            {/* Email */}
            <div>
              <label className="text-sm text-slate-300">Email Address</label>
              <input
                type="email"
                className="input mt-2"
                value={form.email}
                onChange={set('email')}
                placeholder="admin@churnshield.ai"
                required
              />
            </div>

            {/* Password */}
            <div>
              <label className="text-sm text-slate-300">Password</label>
              <div className="relative mt-2">
                <input
                  type={showPwd ? 'text' : 'password'}
                  className="input pr-10"
                  value={form.password}
                  onChange={set('password')}
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPwd((s) => !s)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                >
                  {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Role */}
            <div>
              <label className="text-sm text-slate-300">Role</label>
              <select className="input mt-2" value={form.role} onChange={set('role')}>
                {ROLES.map((r) => <option key={r}>{r}</option>)}
              </select>
            </div>

            {/* Remember me */}
            <div className="flex items-center justify-between text-xs text-slate-400">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" defaultChecked className="rounded" />
                Remember me
              </label>
              <span className="hover:text-white cursor-pointer transition-colors">Forgot Password?</span>
            </div>

            {/* Error */}
            {error && (
              <div className="red-glow rounded-xl px-4 py-3 text-sm text-red-200">
                {error}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="glow-btn w-full py-3 rounded-xl font-semibold flex items-center justify-center gap-2 disabled:opacity-70"
            >
              {loading ? <><Loader2 size={18} className="animate-spin" /> Signing in…</> : 'Login'}
            </button>
          </form>


        </div>
      </div>
    </div>
  )
}
