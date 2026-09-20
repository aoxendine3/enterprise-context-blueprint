import { useState } from 'react'
import { AlertTriangle, CheckCircle, Loader2, Mail, RefreshCw, ShieldAlert, ShieldCheck } from 'lucide-react'
import { predictApi } from '../services/api.js'

const DEFAULT_FORM = {
  customer_id: 'CUST1001',
  age: 28,
  gender: 'Female',
  location: 'Chennai',
  total_orders: 45,
  days_since_last_purchase: 120,
  avg_order_value: 850,
  cart_abandonment_rate: 65,
  website_visits: 24,
  customer_rating: 3,
  payment_method: 'UPI',
  return_count: 2,
  support_tickets: 1,
}

const FIELD_META = {
  customer_id:               { label: 'Customer ID',                type: 'text' },
  age:                       { label: 'Age',                        type: 'number', min: 18, max: 100 },
  gender:                    { label: 'Gender',                     type: 'select', opts: ['Male', 'Female', 'Other'] },
  location:                  { label: 'Location',                   type: 'text' },
  total_orders:              { label: 'Total Orders',               type: 'number', min: 0 },
  days_since_last_purchase:  { label: 'Days Since Last Purchase',   type: 'number', min: 0 },
  avg_order_value:           { label: 'Avg Order Value ($)',        type: 'number', min: 0 },
  cart_abandonment_rate:     { label: 'Cart Abandonment Rate (%)',  type: 'number', min: 0, max: 100 },
  website_visits:            { label: 'Website Visits',             type: 'number', min: 0 },
  customer_rating:           { label: 'Customer Rating (1–5)',      type: 'number', min: 1, max: 5 },
  payment_method:            { label: 'Payment Method',             type: 'select', opts: ['UPI', 'Credit Card', 'Debit Card', 'Net Banking', 'Cash on Delivery'] },
  return_count:              { label: 'Return Count',               type: 'number', min: 0 },
  support_tickets:           { label: 'Support Tickets',            type: 'number', min: 0 },
}

function riskColor(risk) {
  if (!risk) return 'text-slate-300'
  const r = risk.toLowerCase()
  if (r.includes('high'))   return 'text-red-300'
  if (r.includes('medium')) return 'text-yellow-300'
  return 'text-emerald-300'
}

function riskBg(risk) {
  const r = (risk || '').toLowerCase()
  if (r.includes('high'))   return 'red-glow'
  if (r.includes('medium')) return 'yellow-glow'
  return 'green-card'
}

function RiskIcon({ risk }) {
  const r = (risk || '').toLowerCase()
  if (r.includes('high'))   return <ShieldAlert className="text-red-300" />
  if (r.includes('medium')) return <AlertTriangle className="text-yellow-300" />
  return <ShieldCheck className="text-emerald-300" />
}

export default function Prediction() {
  const [form, setForm] = useState(DEFAULT_FORM)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))
  const reset = () => { setForm(DEFAULT_FORM); setResult(null); setError('') }

  const predict = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await predictApi.predict(form)
      setResult(res.data)
    } catch (err) {
      setResult(null)
      setError(err.response?.data?.message || 'Prediction failed. Check live backend and MongoDB connection.')
    } finally {
      setLoading(false)
    }
  }

  const probDeg = result ? Math.min((result.probability / 100) * 180, 175) : 0

  return (
    <div className="grid xl:grid-cols-[1.4fr_.9fr] gap-6">
      {error && <div className="xl:col-span-2 red-glow rounded-xl px-4 py-3 text-sm text-red-200">{error}</div>}
      {/* Form */}
      <div className="glass rounded-2xl p-6">
        <h2 className="text-xl font-bold">Churn Prediction</h2>
        <p className="text-slate-400 mt-1 mb-6">Enter customer details to predict churn probability</p>

        <div className="grid sm:grid-cols-2 gap-4">
          {Object.entries(FIELD_META).map(([key, meta]) => (
            <div key={key}>
              <label className="text-xs text-slate-400 mb-1 block">{meta.label}</label>
              {meta.type === 'select' ? (
                <select className="input" value={form[key]} onChange={set(key)}>
                  {meta.opts.map((o) => <option key={o}>{o}</option>)}
                </select>
              ) : (
                <input
                  type={meta.type}
                  className="input"
                  value={form[key]}
                  min={meta.min}
                  max={meta.max}
                  onChange={set(key)}
                />
              )}
            </div>
          ))}
        </div>

        <div className="flex gap-3 mt-6">
          <button onClick={reset} className="glass px-6 py-3 rounded-xl text-sm font-medium flex items-center gap-2 hover:bg-white/10">
            <RefreshCw size={16} /> Reset
          </button>
          <button
            onClick={predict}
            disabled={loading}
            className="glow-btn flex-1 py-3 rounded-xl font-semibold flex items-center justify-center gap-2"
          >
            {loading ? <><Loader2 size={18} className="animate-spin" /> Predicting…</> : '🔮 Predict Churn'}
          </button>
        </div>
      </div>

      {/* Results */}
      <div className="space-y-5">
        {/* Gauge */}
        <div className="glass rounded-2xl p-6 text-center">
          <h3 className="font-bold mb-5">Prediction Result</h3>

          {result ? (
            <>
              <div className={`${riskBg(result.risk)} rounded-xl px-4 py-3 flex items-center gap-3 mb-5`}>
                <RiskIcon risk={result.risk} />
                <span className={`font-bold ${riskColor(result.risk)}`}>{result.risk}</span>
              </div>

              {/* Semi-circle gauge */}
              <p className="text-slate-400 text-sm mb-3">Churn Probability</p>
              <div className="gauge-wrap mx-auto mb-2">
                <div className="gauge-bg" />
                <div
                  className={`gauge-fill ${result.probability >= 70 ? 'border-red-400' : result.probability >= 35 ? 'border-yellow-400' : 'border-emerald-400'}`}
                  style={{ transform: `rotate(${probDeg - 90}deg)` }}
                />
                <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-4xl font-black">
                  {result.probability}%
                </div>
              </div>

              {/* Feature breakdown */}
              {result.features_used && (
                <div className="mt-5 space-y-2 text-left">
                  <p className="text-xs text-slate-400 font-medium mb-3">Key Factors</p>
                  {[
                    ['Days Since Purchase', result.features_used.days_since_last_purchase],
                    ['Cart Abandonment', `${result.features_used.cart_abandonment_rate}%`],
                    ['Support Tickets', result.features_used.support_tickets],
                    ['Customer Rating', `${result.features_used.customer_rating}/5`],
                  ].map(([label, val]) => (
                    <div key={label} className="flex justify-between text-xs">
                      <span className="text-slate-400">{label}</span>
                      <span className="text-white font-medium">{val}</span>
                    </div>
                  ))}
                </div>
              )}

              <p className="text-xs text-slate-500 mt-4">Model: {result.model_used || 'XGBoost'}</p>
            </>
          ) : (
            <div className="py-8 text-slate-500 text-sm">
              <ShieldCheck size={40} className="mx-auto mb-3 opacity-30" />
              Fill in customer details and click <br /><strong className="text-slate-400">Predict Churn</strong>
            </div>
          )}
        </div>

        {/* Recommended action */}
        {result && (
          <div className="glass rounded-2xl p-5">
            <h3 className="font-bold mb-3">Recommended Action</h3>
            <p className="text-slate-300 text-sm leading-relaxed">{result.action}</p>
            <button className="glow-btn mt-4 px-5 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2">
              <Mail size={16} /> Send Campaign
            </button>
          </div>
        )}

        {/* History hint */}
        <div className="glass rounded-2xl p-5">
          <h3 className="font-bold mb-2">Prediction History</h3>
          <p className="text-slate-400 text-sm">Recent predictions are saved automatically. Upload a dataset for bulk predictions.</p>
          <div className="mt-3 space-y-2">
            {[
              { id: 'CUST1001', prob: 87, risk: 'High Risk' },
              { id: 'CUST1007', prob: 42, risk: 'Medium Risk' },
              { id: 'CUST1012', prob: 15, risk: 'Low Risk' },
            ].map((p) => (
              <div key={p.id} className="flex items-center justify-between text-xs py-1.5 border-b border-white/5 last:border-0">
                <span className="text-slate-300">{p.id}</span>
                <span className={`font-bold ${p.prob >= 70 ? 'text-red-300' : p.prob >= 35 ? 'text-yellow-300' : 'text-emerald-300'}`}>
                  {p.prob}%
                </span>
                <span className="text-slate-500">{p.risk}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
