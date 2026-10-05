import { useEffect, useMemo, useState } from 'react'
import {
  Bell,
  CheckCircle,
  Copy,
  Eye,
  EyeOff,
  Key,
  Loader2,
  Lock,
  RefreshCcw,
  Save,
  Shield,
  Sliders,
  User,
} from 'lucide-react'
import { settingsApi } from '../services/api.js'

const EMPTY_SETTINGS = {
  profile: {
    name: '',
    email: '',
    role: 'Admin',
    company: '',
  },
  notifications: {
    email_alerts: false,
    high_risk_threshold: 70,
    weekly_report: false,
    model_retrain_alert: false,
  },
  model: {
    threshold: 0.5,
    auto_retrain: false,
    retrain_frequency: 'monthly',
  },
  security: {
    api_key: 'cs-api-••••••••••••••••••••••••',
    api_key_masked: 'cs-api-••••••••••••••••••••••••',
    last_api_key_rotation: '',
  },
}

function mergeSettings(data = {}) {
  return {
    profile: {
      ...EMPTY_SETTINGS.profile,
      ...(data.profile || {}),
    },
    notifications: {
      ...EMPTY_SETTINGS.notifications,
      ...(data.notifications || {}),
    },
    model: {
      ...EMPTY_SETTINGS.model,
      ...(data.model || {}),
    },
    security: {
      ...EMPTY_SETTINGS.security,
      ...(data.security || {}),
    },
  }
}

export default function Settings() {
  const [settings, setSettings] = useState(EMPTY_SETTINGS)

  const [passwords, setPasswords] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  })

  const [showPasswords, setShowPasswords] = useState({
    current_password: false,
    new_password: false,
    confirm_password: false,
  })

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [securityBusy, setSecurityBusy] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [activeTab, setActiveTab] = useState('profile')
  const [apiVisible, setApiVisible] = useState(false)
  const [attestationKey, setAttestationKey] = useState('')

  const tabs = useMemo(
    () => [
      { key: 'profile', label: 'Profile', Icon: User },
      { key: 'notifications', label: 'Notifications', Icon: Bell },
      { key: 'model', label: 'Model Config', Icon: Sliders },
      { key: 'security', label: 'Security', Icon: Lock },
    ],
    []
  )

  useEffect(() => {
    let ignore = false

    settingsApi
      .get()
      .then((res) => {
        if (!ignore) {
          setSettings(mergeSettings(res.data))
        }
      })
      .catch((err) => {
        if (!ignore) {
          setError(err.response?.data?.message || 'Unable to load live MongoDB settings.')
        }
      })
      .finally(() => {
        if (!ignore) {
          setLoading(false)
        }
      })

    settingsApi
      .getAttestationKey()
      .then((res) => {
        if (!ignore) {
          setAttestationKey(res.data.public_key || '')
        }
      })
      .catch((err) => {
        console.warn('Failed to load attestation public key:', err)
      })

    return () => {
      ignore = true
    }
  }, [])

  const setNested = (section, key, value) => {
    setSettings((s) => ({
      ...s,
      [section]: {
        ...s[section],
        [key]: value,
      },
    }))
  }

  const setPasswordValue = (key, value) => {
    setPasswords((p) => ({
      ...p,
      [key]: value,
    }))
  }

  const togglePasswordView = (key) => {
    setShowPasswords((p) => ({
      ...p,
      [key]: !p[key],
    }))
  }

  const showMessage = (message, type = 'success') => {
    if (type === 'success') {
      setSuccess(message)
      setError('')
    } else {
      setError(message)
      setSuccess('')
    }

    window.clearTimeout(showMessage.timer)
    showMessage.timer = window.setTimeout(() => {
      setSuccess('')
      setError('')
    }, 3500)
  }

  const save = async () => {
    setSaving(true)

    try {
      const payload = {
        profile: settings.profile,
        notifications: settings.notifications,
        model: settings.model,
      }

      const res = await settingsApi.update(payload)
      setSettings(mergeSettings(res.data.data || payload))
      showMessage('Settings saved successfully to MongoDB.')
    } catch (err) {
      showMessage(err.response?.data?.message || 'Unable to save settings to MongoDB.', 'error')
    } finally {
      setSaving(false)
    }
  }

  const updatePassword = async () => {
    if (!passwords.current_password || !passwords.new_password || !passwords.confirm_password) {
      showMessage('Please fill all password fields.', 'error')
      return
    }

    if (passwords.new_password.length < 8) {
      showMessage('New password must be minimum 8 characters.', 'error')
      return
    }

    if (passwords.new_password !== passwords.confirm_password) {
      showMessage('New password and confirm password do not match.', 'error')
      return
    }

    setSecurityBusy(true)

    try {
      const res = await settingsApi.changePassword(passwords)

      setPasswords({
        current_password: '',
        new_password: '',
        confirm_password: '',
      })

      setShowPasswords({
        current_password: false,
        new_password: false,
        confirm_password: false,
      })

      showMessage(res.data.message || 'Password updated successfully.')
    } catch (err) {
      showMessage(err.response?.data?.message || 'Unable to update password.', 'error')
    } finally {
      setSecurityBusy(false)
    }
  }

  const revealApiKey = async () => {
    setSecurityBusy(true)

    try {
      const res = await settingsApi.revealApiKey()

      setApiVisible(true)
      setNested('security', 'api_key', res.data.api_key)
      setNested('security', 'api_key_masked', res.data.api_key_masked)

      showMessage('API key revealed.')
    } catch (err) {
      showMessage(err.response?.data?.message || 'Unable to reveal API key.', 'error')
    } finally {
      setSecurityBusy(false)
    }
  }

  const regenerateApiKey = async () => {
    setSecurityBusy(true)

    try {
      const res = await settingsApi.regenerateApiKey()

      setApiVisible(true)
      setSettings((s) => ({
        ...s,
        security: {
          ...s.security,
          api_key: res.data.api_key,
          api_key_masked: res.data.api_key_masked,
          last_api_key_rotation: new Date().toISOString(),
        },
      }))

      showMessage('New API key generated and saved.')
    } catch (err) {
      showMessage(err.response?.data?.message || 'Unable to regenerate API key.', 'error')
    } finally {
      setSecurityBusy(false)
    }
  }

  const copyApiKey = async () => {
    try {
      await navigator.clipboard.writeText(settings.security.api_key)
      showMessage('API key copied to clipboard.')
    } catch {
      showMessage('Clipboard permission denied. Select and copy the key manually.', 'error')
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 size={36} className="animate-spin text-cyan-300" />
      </div>
    )
  }

  const displayedApiKey = apiVisible
    ? settings.security.api_key
    : settings.security.api_key_masked

  return (
    <div className="space-y-6">
      {error && (
        <div className="red-glow rounded-xl px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      {success && (
        <div className="green-card rounded-xl px-4 py-3 text-sm text-emerald-200">
          {success}
        </div>
      )}

      <div className="glass rounded-2xl p-2 flex gap-1 overflow-x-auto">
        {tabs.map(({ key, label, Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition ${
              activeTab === key
                ? 'nav-active'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      <div className="glass rounded-2xl p-6">
        {activeTab === 'profile' && (
          <Section title="Profile Information" icon={User}>
            <div className="grid sm:grid-cols-2 gap-5">
              <Field label="Full Name">
                <input
                  className="input"
                  value={settings.profile.name}
                  onChange={(e) => setNested('profile', 'name', e.target.value)}
                />
              </Field>

              <Field label="Email Address">
                <input
                  type="email"
                  className="input"
                  value={settings.profile.email}
                  onChange={(e) => setNested('profile', 'email', e.target.value)}
                />
              </Field>

              <Field label="Role">
                <select
                  className="input"
                  value={settings.profile.role}
                  onChange={(e) => setNested('profile', 'role', e.target.value)}
                >
                  <option>Admin</option>
                  <option>Data Analyst</option>
                  <option>Manager</option>
                </select>
              </Field>

              <Field label="Company">
                <input
                  className="input"
                  value={settings.profile.company}
                  onChange={(e) => setNested('profile', 'company', e.target.value)}
                />
              </Field>
            </div>

            <div className="mt-6 pt-6 border-t border-white/10">
              <p className="text-sm text-slate-300 mb-3">Profile Preview</p>

              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-full glow-btn flex items-center justify-center text-2xl font-bold">
                  {(settings.profile.name || 'U').charAt(0).toUpperCase()}
                </div>

                <div>
                  <p className="font-semibold">
                    {settings.profile.name || 'ChurnShield User'}
                  </p>
                  <p className="text-sm text-slate-400">
                    {settings.profile.email || 'No email'} · {settings.profile.role}
                  </p>
                </div>
              </div>
            </div>
          </Section>
        )}

        {activeTab === 'notifications' && (
          <Section title="Notification Preferences" icon={Bell}>
            <div className="space-y-5">
              <Toggle
                label="Email Alerts"
                desc="Receive email notifications for high-risk customers"
                value={settings.notifications.email_alerts}
                onChange={(v) => setNested('notifications', 'email_alerts', v)}
              />

              <Toggle
                label="Weekly Report Email"
                desc="Get a weekly churn summary report in your inbox"
                value={settings.notifications.weekly_report}
                onChange={(v) => setNested('notifications', 'weekly_report', v)}
              />

              <Toggle
                label="Model Retrain Alert"
                desc="Be notified when model retraining is scheduled"
                value={settings.notifications.model_retrain_alert}
                onChange={(v) => setNested('notifications', 'model_retrain_alert', v)}
              />

              <div className="pt-4 border-t border-white/10">
                <label className="text-sm text-slate-300 block mb-2">
                  High-Risk Alert Threshold (%)
                </label>

                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min={50}
                    max={95}
                    step={5}
                    value={settings.notifications.high_risk_threshold}
                    onChange={(e) =>
                      setNested(
                        'notifications',
                        'high_risk_threshold',
                        Number(e.target.value)
                      )
                    }
                    className="flex-1 accent-indigo-500"
                  />

                  <span className="text-cyan-300 font-bold w-12 text-center">
                    {settings.notifications.high_risk_threshold}%
                  </span>
                </div>

                <p className="text-xs text-slate-500 mt-1">
                  Alert when predicted churn probability exceeds this value.
                </p>
              </div>
            </div>
          </Section>
        )}

        {activeTab === 'model' && (
          <Section title="Model Configuration" icon={Sliders}>
            <div className="space-y-6">
              <div>
                <label className="text-sm text-slate-300 block mb-2">
                  Churn Probability Threshold
                </label>

                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min={0.3}
                    max={0.8}
                    step={0.05}
                    value={settings.model.threshold}
                    onChange={(e) =>
                      setNested('model', 'threshold', Number(e.target.value))
                    }
                    className="flex-1 accent-indigo-500"
                  />

                  <span className="text-cyan-300 font-bold w-16 text-center">
                    {Number(settings.model.threshold).toFixed(2)}
                  </span>
                </div>

                <p className="text-xs text-slate-500 mt-1">
                  Customers above this threshold are flagged as likely churners.
                </p>
              </div>

              <Toggle
                label="Auto Retrain"
                desc="Automatically retrain the model when new data is uploaded"
                value={settings.model.auto_retrain}
                onChange={(v) => setNested('model', 'auto_retrain', v)}
              />

              <Field label="Retrain Frequency">
                <select
                  className="input max-w-xs"
                  value={settings.model.retrain_frequency}
                  onChange={(e) =>
                    setNested('model', 'retrain_frequency', e.target.value)
                  }
                >
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="quarterly">Quarterly</option>
                  <option value="manual">Manual Only</option>
                </select>
              </Field>

              <div className="glass rounded-xl p-4 border border-cyan-500/20">
                <div className="flex items-center gap-2 mb-2">
                  <Shield size={16} className="text-cyan-300" />
                  <span className="text-sm font-medium">Current Model</span>
                </div>

                <div className="grid sm:grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-slate-400">Type:</span>{' '}
                    <span className="text-white">XGBoost / Rule-based fallback</span>
                  </div>

                  <div>
                    <span className="text-slate-400">Live Source:</span>{' '}
                    <span className="text-emerald-300">MongoDB Customers</span>
                  </div>

                  <div>
                    <span className="text-slate-400">Threshold:</span>{' '}
                    <span className="text-white">
                      {Number(settings.model.threshold).toFixed(2)}
                    </span>
                  </div>

                  <div>
                    <span className="text-slate-400">Retrain:</span>{' '}
                    <span className="text-white capitalize">
                      {settings.model.retrain_frequency}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </Section>
        )}

        {activeTab === 'security' && (
          <Section title="Security Settings" icon={Lock}>
            <div className="space-y-6">
              <div>
                <h4 className="text-sm font-medium text-slate-300 mb-4 flex items-center gap-2">
                  <Key size={16} className="text-cyan-300" />
                  Change Password
                </h4>

                <div className="grid sm:grid-cols-3 gap-4">
                  <Field label="Current Password">
                    <PasswordInput
                      value={passwords.current_password}
                      visible={showPasswords.current_password}
                      placeholder="Current password"
                      onChange={(value) => setPasswordValue('current_password', value)}
                      onToggle={() => togglePasswordView('current_password')}
                    />
                  </Field>

                  <Field label="New Password">
                    <PasswordInput
                      value={passwords.new_password}
                      visible={showPasswords.new_password}
                      placeholder="Minimum 8 characters"
                      onChange={(value) => setPasswordValue('new_password', value)}
                      onToggle={() => togglePasswordView('new_password')}
                    />
                  </Field>

                  <Field label="Confirm New Password">
                    <PasswordInput
                      value={passwords.confirm_password}
                      visible={showPasswords.confirm_password}
                      placeholder="Confirm password"
                      onChange={(value) => setPasswordValue('confirm_password', value)}
                      onToggle={() => togglePasswordView('confirm_password')}
                    />
                  </Field>
                </div>

                <button
                  onClick={updatePassword}
                  disabled={securityBusy}
                  className="mt-4 glow-btn px-6 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-60"
                >
                  {securityBusy ? 'Updating…' : 'Update Password'}
                </button>
              </div>

              <div className="pt-6 border-t border-white/10">
                <h4 className="text-sm font-medium text-slate-300 mb-4">
                  API Key
                </h4>

                <div className="flex flex-col lg:flex-row gap-3 max-w-4xl">
                  <input
                    className="input font-mono text-xs"
                    value={displayedApiKey}
                    readOnly
                  />

                  <div className="flex gap-2">
                    <button
                      onClick={revealApiKey}
                      disabled={securityBusy}
                      className="glass px-4 py-2.5 rounded-xl text-sm whitespace-nowrap hover:bg-white/10 flex items-center gap-2"
                    >
                      <Eye size={15} />
                      Reveal
                    </button>

                    <button
                      onClick={copyApiKey}
                      className="glass px-4 py-2.5 rounded-xl text-sm whitespace-nowrap hover:bg-white/10 flex items-center gap-2"
                    >
                      <Copy size={15} />
                      Copy
                    </button>

                    <button
                      onClick={regenerateApiKey}
                      disabled={securityBusy}
                      className="red-glow-btn px-4 py-2.5 rounded-xl text-sm whitespace-nowrap flex items-center gap-2"
                    >
                      <RefreshCcw size={15} />
                      Regenerate
                    </button>
                  </div>
                </div>

                <p className="text-xs text-slate-500 mt-2">
                  Last rotation:{' '}
                  {settings.security.last_api_key_rotation
                    ? new Date(settings.security.last_api_key_rotation).toLocaleString()
                    : 'Not available'}
                </p>
              </div>

              {attestationKey && (
                <div className="pt-6 border-t border-white/10">
                  <h4 className="text-sm font-medium text-slate-300 mb-2">
                    Xoras Machine Attestation Public Key
                  </h4>
                  <p className="text-xs text-slate-400 mb-3 leading-relaxed">
                    This public key represents this specific local workstation's hardware attestation identity (RSA-SHA256). All human safety review overrides are signed by the corresponding private key on disk.
                  </p>
                  <div className="relative">
                    <pre className="font-mono text-[10px] bg-slate-950/60 border border-white/5 rounded-xl p-4 text-cyan-300/80 overflow-x-auto max-h-36 scrollbar">
                      {attestationKey}
                    </pre>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(attestationKey)
                        showMessage('Attestation public key copied to clipboard!', 'success')
                      }}
                      className="absolute top-2 right-2 p-1.5 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 text-slate-300 transition"
                      title="Copy Key"
                    >
                      <Copy size={12} />
                    </button>
                  </div>
                </div>
              )}

              <div className="pt-6 border-t border-white/10">
                <h4 className="text-sm font-medium text-slate-300 mb-4">
                  Active Session
                </h4>

                <div className="flex items-center justify-between bg-white/5 rounded-xl px-4 py-3">
                  <div>
                    <p className="text-sm font-medium">Current browser session</p>
                    <p className="text-xs text-slate-400">
                      Secured using JWT token from localStorage
                    </p>
                  </div>

                  <span className="badge bg-emerald-500/15 text-emerald-300 border border-emerald-500/25">
                    Current
                  </span>
                </div>
              </div>
            </div>
          </Section>
        )}

        {activeTab !== 'security' && (
          <div className="mt-8 pt-6 border-t border-white/10 flex items-center gap-4">
            <button
              onClick={save}
              disabled={saving}
              className="glow-btn px-8 py-3 rounded-xl font-semibold flex items-center gap-2 disabled:opacity-70"
            >
              {saving ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Saving…
                </>
              ) : (
                <>
                  <Save size={16} />
                  Save Changes
                </>
              )}
            </button>

            {success && (
              <span className="text-emerald-300 text-sm">
                <CheckCircle size={15} className="inline mr-1" />
                Saved
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function Section({ title, icon: Icon, children }) {
  return (
    <div>
      <h3 className="text-lg font-bold mb-6 flex items-center gap-2">
        <Icon size={20} className="text-cyan-300" />
        {title}
      </h3>

      {children}
    </div>
  )
}

function Field({ label, children }) {
  return (
    <div>
      <label className="text-xs text-slate-400 mb-1.5 block">
        {label}
      </label>

      {children}
    </div>
  )
}

function PasswordInput({ value, visible, placeholder, onChange, onToggle }) {
  return (
    <div className="relative">
      <input
        type={visible ? 'text' : 'password'}
        className="input pr-12"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        autoComplete="new-password"
      />

      <button
        type="button"
        onClick={onToggle}
        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-cyan-300 transition"
        aria-label={visible ? 'Hide password' : 'Show password'}
      >
        {visible ? <EyeOff size={18} /> : <Eye size={18} />}
      </button>
    </div>
  )
}

function Toggle({ label, desc, value, onChange }) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-white/5">
      <div>
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-slate-400 mt-0.5">{desc}</p>
      </div>

      <button
        type="button"
        onClick={() => onChange(!value)}
        className={`relative w-12 h-6 rounded-full transition-colors shrink-0 ml-4 ${
          value ? 'bg-indigo-500' : 'bg-slate-700'
        }`}
      >
        <div
          className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${
            value ? 'translate-x-7' : 'translate-x-1'
          }`}
        />
      </button>
    </div>
  )
}