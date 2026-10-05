import { useEffect, useState } from 'react'
import { Activity, DollarSign, Loader2, Target, Users, Zap } from 'lucide-react'
import {
  AreaChart, Area,
  BarChart, Bar,
  LineChart, Line,
  PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import StatCard from '../components/StatCard.jsx'
import { dashboardApi } from '../services/api.js'

const RISK_COLORS = ['#ff465c', '#ffb020', '#19c37d', '#2f80ed']

const EMPTY = {
  total_customers: 0,
  active_customers: 0,
  churned_customers: 0,
  churn_risk: 0,
  revenue_at_risk: 0,
  model_accuracy: 0,
  monthly_savings: 0,
  predictions_today: 0,
  trend: [],
  risk_distribution: [],
}

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    dashboardApi.get()
      .then((res) => setData(res.data))
      .catch((err) => {
        setError(err.response?.data?.message || 'Unable to load live MongoDB dashboard data.')
        setData(EMPTY)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 size={36} className="animate-spin text-cyan-300" />
      </div>
    )
  }

  const d = data || EMPTY

  return (
    <div className="space-y-6">
      {error && <div className="red-glow rounded-xl px-4 py-3 text-sm text-red-200">{error}</div>}
      {/* Stat cards */}
      <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-5">
        <StatCard
          icon={Users} title="Total Customers"
          value={d.total_customers.toLocaleString()}
          delta="+ 12.5% from last month" tone="blue" trend="up"
        />
        <StatCard
          icon={Activity} title="Active Customers"
          value={d.active_customers.toLocaleString()}
          delta="+ 8.2% from last month" tone="green" trend="up"
        />
        <StatCard
          icon={Target} title="Churned Customers"
          value={d.churned_customers.toLocaleString()}
          delta="- 15.7% from last month" tone="red" trend="down"
        />
        <StatCard
          icon={DollarSign} title="Churn Risk"
          value={`${d.churn_risk}%`}
          delta="- 2.3% from last month" tone="red" trend="down"
        />
      </div>

      {/* Secondary metrics */}
      <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-5">
        <StatCard
          icon={DollarSign} title="Revenue at Risk"
          value={`$${(d.revenue_at_risk / 1000).toFixed(0)}K`}
          delta="Updated today" tone="yellow"
        />
        <StatCard
          icon={Zap} title="Model Accuracy"
          value={`${d.model_accuracy}%`}
          delta="XGBoost Classifier" tone="purple"
        />
        <StatCard
          icon={DollarSign} title="Monthly Savings"
          value={`$${(d.monthly_savings / 1000).toFixed(0)}K`}
          delta="Via retention actions" tone="green" trend="up"
        />
        <StatCard
          icon={Activity} title="Predictions Today"
          value={d.predictions_today.toLocaleString()}
          delta="Real-time scoring" tone="blue"
        />
      </div>

      {/* Charts row */}
      <div className="grid xl:grid-cols-3 gap-5">
        {/* Churn risk trend */}
        <Panel title="Churn Risk Trend" value="Last 12 Months" className="xl:col-span-2">
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={d.trend}>
              <defs>
                <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6d5dfc" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#6d5dfc" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="month" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} unit="%" />
              <Tooltip
                contentStyle={{ background: '#0c1427', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
                itemStyle={{ color: '#ffffff' }}
                labelStyle={{ color: '#94a3b8' }}
              />
              <Area dataKey="risk" stroke="#6d5dfc" strokeWidth={2.5} fill="url(#riskGrad)" name="Churn Risk %" />
            </AreaChart>
          </ResponsiveContainer>
        </Panel>

        {/* Risk distribution pie */}
        <Panel title="Risk Distribution" value="">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={d.risk_distribution}
                dataKey="value"
                innerRadius={55}
                outerRadius={90}
                paddingAngle={3}
              >
                {d.risk_distribution.map((_, i) => (
                  <Cell key={i} fill={RISK_COLORS[i]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#0c1427', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
                itemStyle={{ color: '#ffffff' }}
                labelStyle={{ color: '#94a3b8' }}
                formatter={(val) => [val.toLocaleString(), '']}
              />
              <Legend
                formatter={(val) => <span style={{ fontSize: 11, color: '#94a3b8' }}>{val}</span>}
              />
            </PieChart>
          </ResponsiveContainer>
        </Panel>
      </div>

      {/* Customer growth */}
      <Panel title="Customer Growth" value="Jan – Dec">
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={d.trend}>
            <defs>
              <linearGradient id="custGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#19c37d" stopOpacity={0.9} />
                <stop offset="100%" stopColor="#19c37d" stopOpacity={0.3} />
              </linearGradient>
            </defs>
            <XAxis dataKey="month" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ background: '#0c1427', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
              itemStyle={{ color: '#ffffff' }}
              labelStyle={{ color: '#94a3b8' }}
            />
            <Bar dataKey="customers" fill="url(#custGrad)" radius={[4, 4, 0, 0]} name="Customers" />
          </BarChart>
        </ResponsiveContainer>
      </Panel>
    </div>
  )
}

function Panel({ title, value, children, className = '' }) {
  return (
    <div className={`glass rounded-2xl p-5 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-slate-400">{title}</p>
        {value && <span className="text-xs text-slate-500">{value}</span>}
      </div>
      {children}
    </div>
  )
}
