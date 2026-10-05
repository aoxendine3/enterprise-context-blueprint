import { useEffect, useState } from 'react'
import { Eye, Filter, Loader2, Search } from 'lucide-react'
import { riskApi } from '../services/api.js'

const RISK_FILTERS = ['all', 'High Risk', 'Medium Risk', 'Low Risk']

const EMPTY_SUMMARY = {
  high_risk: 0, medium_risk: 0, low_risk: 0, loyal: 0,
}

function riskBadge(risk) {
  const r = (risk || '').toLowerCase()
  if (r.includes('high'))   return 'bg-red-500/20 text-red-200 border border-red-500/30'
  if (r.includes('medium')) return 'bg-yellow-500/20 text-yellow-200 border border-yellow-500/30'
  if (r.includes('low'))    return 'bg-emerald-500/20 text-emerald-200 border border-emerald-500/30'
  return 'bg-blue-500/20 text-blue-200 border border-blue-500/30'
}

function probColor(prob) {
  if (prob >= 70) return 'text-red-300 font-bold'
  if (prob >= 35) return 'text-yellow-300 font-bold'
  return 'text-emerald-300 font-bold'
}

export default function RiskAnalysis() {
  const [customers, setCustomers] = useState([])
  const [summary, setSummary] = useState(EMPTY_SUMMARY)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [riskFilter, setRiskFilter] = useState('all')
  const [search, setSearch] = useState('')

  useEffect(() => {
    riskApi.get({ risk: riskFilter })
      .then((res) => {
        setCustomers(res.data.customers || [])
        if (res.data.summary) setSummary(res.data.summary)
      })
      .catch((err) => {
        setError(err.response?.data?.message || 'Unable to load live MongoDB customer risk data.')
        setCustomers([])
        setSummary(EMPTY_SUMMARY)
      })
      .finally(() => setLoading(false))
  }, [riskFilter])

  const filtered = customers.filter((c) => {
    const q = search.toLowerCase()
    return !q || c.name?.toLowerCase().includes(q) || c.id?.toLowerCase().includes(q)
  })

  return (
    <div className="space-y-6">
      {error && <div className="red-glow rounded-xl px-4 py-3 text-sm text-red-200">{error}</div>}
      {/* Summary chips */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        {[
          { label: 'High Risk',       value: summary.high_risk,   color: 'border-red-500/30    bg-red-500/10    text-red-300' },
          { label: 'Medium Risk',     value: summary.medium_risk, color: 'border-yellow-500/30 bg-yellow-500/10 text-yellow-300' },
          { label: 'Low Risk',        value: summary.low_risk,    color: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300' },
          { label: 'Loyal Customers', value: summary.loyal,       color: 'border-blue-500/30   bg-blue-500/10   text-blue-300' },
        ].map(({ label, value, color }) => (
          <div key={label} className={`glass rounded-xl p-4 border ${color.split(' ')[0]}`}>
            <p className="text-xs text-slate-400">{label}</p>
            <h3 className={`text-3xl font-bold mt-1 ${color.split(' ')[2]}`}>
              {value.toLocaleString()}
            </h3>
          </div>
        ))}
      </div>

      {/* Table card */}
      <div className="glass rounded-2xl p-6">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-6">
          <div>
            <h2 className="text-xl font-bold">Customer Risk Analysis</h2>
            <p className="text-slate-400 text-sm">Customers grouped by predicted churn risk</p>
          </div>
          <div className="sm:ml-auto flex flex-wrap gap-3">
            {/* Search */}
            <div className="flex items-center gap-2 glass rounded-xl px-3 py-2 w-52">
              <Search size={14} className="text-slate-500 shrink-0" />
              <input
                className="bg-transparent outline-none text-sm w-full placeholder-slate-500"
                placeholder="Search customer…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            {/* Filter */}
            <div className="flex items-center gap-2 glass rounded-xl px-3 py-2">
              <Filter size={14} className="text-slate-500" />
              <select
                className="bg-transparent outline-none text-sm text-slate-300"
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
              >
                {RISK_FILTERS.map((f) => <option key={f} className="bg-slate-900">{f}</option>)}
              </select>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-16">
            <Loader2 size={32} className="animate-spin text-cyan-300" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[700px]">
              <thead>
                <tr className="bg-slate-950/70 text-slate-400 text-xs uppercase tracking-wide">
                  {['Customer ID', 'Name', 'Orders', 'Last Purchase', 'Probability', 'Risk Level', 'Revenue', 'Action'].map((h) => (
                    <th key={h} className="text-left px-4 py-3 first:rounded-l-lg last:rounded-r-lg">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-center py-12 text-slate-500">No customers found.</td>
                  </tr>
                ) : filtered.map((c) => (
                  <tr key={c.id} className="table-row">
                    <td className="px-4 py-3 font-mono text-xs text-slate-300">{c.id}</td>
                    <td className="px-4 py-3 font-medium">{c.name}</td>
                    <td className="px-4 py-3 text-slate-300">{c.orders}</td>
                    <td className="px-4 py-3 text-slate-400">{c.last}</td>
                    <td className="px-4 py-3">
                      <span className={probColor(c.prob || c.probability)}>{c.prob || c.probability}%</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2.5 py-1 rounded-lg text-xs font-medium ${riskBadge(c.risk)}`}>{c.risk}</span>
                    </td>
                    <td className="px-4 py-3 text-slate-300">
                      {c.value ? `$${c.value.toLocaleString()}` : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <button className="px-3 py-1 rounded-lg bg-cyan-500/10 text-cyan-300 text-xs hover:bg-cyan-500/20 flex items-center gap-1.5">
                        <Eye size={12} /> View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <p className="text-slate-400 text-xs mt-5">
          Showing {filtered.length} of {customers.length} customers
        </p>
      </div>
    </div>
  )
}
