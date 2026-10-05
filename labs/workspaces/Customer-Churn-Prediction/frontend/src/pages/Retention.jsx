import { useEffect, useState } from 'react'
import { Bot, Crown, Gift, Loader2, Shield, Users, ArrowRight, CheckCircle } from 'lucide-react'
import { retentionApi } from '../services/api.js'

const SEGMENT_META = {
  'High Risk':        { icon: Gift,   color: 'text-red-300',     bg: 'bg-red-500/10',    border: 'border-red-500/25' },
  'Medium Risk':      { icon: Crown,  color: 'text-yellow-300',  bg: 'bg-yellow-500/10', border: 'border-yellow-500/25' },
  'Low Risk':         { icon: Shield, color: 'text-emerald-300', bg: 'bg-emerald-500/10', border: 'border-emerald-500/25' },
  'Loyal Customers':  { icon: Users,  color: 'text-blue-300',    bg: 'bg-blue-500/10',   border: 'border-blue-500/25' },
}

const EMPTY = {
  strategies: [],
  ai_recommendation: { headline: 'No live data loaded', message: 'Connect MongoDB and upload customers to generate retention recommendations.', estimated_roi: '—' },
}

export default function Retention() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState(null)

  useEffect(() => {
    retentionApi.get()
      .then((res) => setData(res.data))
      .catch((err) => {
        setError(err.response?.data?.message || 'Unable to load live MongoDB retention data.')
        setData(EMPTY)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 size={36} className="animate-spin text-cyan-300" />
      </div>
    )
  }

  const d = data || EMPTY

  return (
    <div className="space-y-6">
      {error && <div className="red-glow rounded-xl px-4 py-3 text-sm text-red-200">{error}</div>}
      {/* Strategy cards */}
      <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-5">
        {d.strategies.map((strategy) => {
          const meta = SEGMENT_META[strategy.segment] || SEGMENT_META['Low Risk']
          const Icon = meta.icon
          const isOpen = expanded === strategy.segment

          return (
            <div
              key={strategy.segment}
              className={`glass rounded-2xl p-6 card-3d border ${meta.border} flex flex-col`}
            >
              {/* Header */}
              <div className={`w-12 h-12 rounded-xl ${meta.bg} flex items-center justify-center mb-4`}>
                <Icon size={22} className={meta.color} />
              </div>
              <h3 className="font-bold text-lg">{strategy.segment}</h3>
              <p className={`text-2xl font-black mt-1 ${meta.color}`}>
                {strategy.count.toLocaleString()}
                <span className="text-sm font-normal text-slate-400 ml-1">customers</span>
              </p>

              {/* Metrics */}
              <div className="grid grid-cols-2 gap-3 mt-4">
                <div className="bg-white/5 rounded-xl p-3 text-center">
                  <div className={`text-xl font-bold ${meta.color}`}>{strategy.expected_recovery}%</div>
                  <div className="text-xs text-slate-400 mt-0.5">Recovery Est.</div>
                </div>
                <div className="bg-white/5 rounded-xl p-3 text-center">
                  <div className={`text-xl font-bold ${meta.color}`}>
                    ${(strategy.revenue_impact / 1000).toFixed(0)}K
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">Impact</div>
                </div>
              </div>

              {/* Actions */}
              <div className="mt-4 flex-1">
                {isOpen ? (
                  <ul className="space-y-2">
                    {strategy.actions.map((action, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
                        <CheckCircle size={13} className={`${meta.color} shrink-0 mt-0.5`} />
                        {action}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-400 truncate-2">
                    {strategy.actions[0]}
                  </p>
                )}
              </div>

              <button
                onClick={() => setExpanded(isOpen ? null : strategy.segment)}
                className={`mt-4 text-sm flex items-center gap-1 ${meta.color} hover:opacity-80 transition`}
              >
                {isOpen ? 'Show less' : 'View strategy'}
                <ArrowRight size={14} className={isOpen ? 'rotate-90' : ''} />
              </button>
            </div>
          )
        })}
      </div>

      {/* AI Recommendation */}
      <div className="glass rounded-2xl p-6">
        <div className="flex items-start gap-5">
          <div className="w-16 h-16 rounded-2xl bg-cyan-500/15 flex items-center justify-center text-cyan-300 shrink-0">
            <Bot size={32} />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h3 className="text-xl font-bold">AI Recommendation</h3>
              <span className="badge bg-cyan-500/15 text-cyan-300 border border-cyan-500/25">
                ROI: {d.ai_recommendation.estimated_roi}
              </span>
            </div>
            <h4 className="text-cyan-300 font-semibold mb-2">{d.ai_recommendation.headline}</h4>
            <p className="text-slate-300 leading-relaxed">{d.ai_recommendation.message}</p>
          </div>
        </div>
      </div>

      {/* Email campaign builder */}
      <div className="glass rounded-2xl p-6">
        <h3 className="font-bold mb-4">Quick Campaign Builder</h3>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Win-Back Email',       desc: 'For High Risk customers. 20% discount + free shipping offer.' },
            { label: 'Loyalty Reward',       desc: 'For Medium Risk. Double points + personalised deals.' },
            { label: 'Engagement Nudge',     desc: 'For Low Risk. Newsletter + new arrivals spotlight.' },
            { label: 'VIP Upgrade',          desc: 'For Loyal Customers. Exclusive membership benefits.' },
          ].map(({ label, desc }) => (
            <div key={label} className="bg-white/5 rounded-xl p-4 hover:bg-white/8 transition cursor-pointer group">
              <h4 className="font-semibold text-sm group-hover:text-cyan-300 transition">{label}</h4>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">{desc}</p>
              <button className="mt-3 text-xs text-cyan-300 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition">
                Launch <ArrowRight size={12} />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
