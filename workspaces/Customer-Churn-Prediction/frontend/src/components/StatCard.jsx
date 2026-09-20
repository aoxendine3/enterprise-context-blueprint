import { motion } from 'framer-motion'
import { TrendingDown, TrendingUp } from 'lucide-react'

const TONE = {
  blue:   { text: 'text-cyan-300',    bg: 'bg-cyan-500/10' },
  green:  { text: 'text-emerald-300', bg: 'bg-emerald-500/10' },
  red:    { text: 'text-red-300',     bg: 'bg-red-500/10' },
  purple: { text: 'text-purple-300',  bg: 'bg-purple-500/10' },
  yellow: { text: 'text-yellow-300',  bg: 'bg-yellow-500/10' },
}

export default function StatCard({ icon: Icon, title, value, delta, tone = 'blue', trend = 'up' }) {
  const { text, bg } = TONE[tone] || TONE.blue
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass card-3d rounded-2xl p-5"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-sm text-slate-400 truncate">{title}</p>
          <h3 className="text-3xl font-bold mt-2 tracking-tight">{value}</h3>
        </div>
        <div className={`w-11 h-11 rounded-xl ${bg} flex items-center justify-center ${text} shrink-0 ml-3`}>
          {Icon && <Icon size={22} />}
        </div>
      </div>
      {delta && (
        <p className={`text-xs mt-4 flex items-center gap-1 ${text}`}>
          {trend === 'up' ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
          {delta}
        </p>
      )}
    </motion.div>
  )
}
