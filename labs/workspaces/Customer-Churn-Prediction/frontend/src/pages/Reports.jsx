import { useState } from 'react'
import { CheckCircle, Download, FileSpreadsheet, FileText, Loader2 } from 'lucide-react'
import { reportsApi } from '../services/api.js'

const REPORTS = [
  {
    id: 'full',
    title: 'Full Prediction Report',
    desc: 'Complete churn prediction results for all customers including probability scores, risk levels, and recommended actions.',
    format: 'CSV',
    icon: FileSpreadsheet,
    color: 'text-emerald-300',
    bg: 'bg-emerald-500/10',
  },
  {
    id: 'risk',
    title: 'Customer Risk Report',
    desc: 'Detailed breakdown of customers by risk segment — High, Medium, Low — with contact details and probability scores.',
    format: 'CSV',
    icon: FileSpreadsheet,
    color: 'text-cyan-300',
    bg: 'bg-cyan-500/10',
  },
  {
    id: 'accuracy',
    title: 'Model Accuracy Report',
    desc: 'XGBoost model performance metrics over time including accuracy, precision, recall, F1 score, and ROC-AUC.',
    format: 'CSV',
    icon: FileText,
    color: 'text-purple-300',
    bg: 'bg-purple-500/10',
  },
  {
    id: 'monthly',
    title: 'Monthly Churn Report',
    desc: 'Month-by-month churn rate trends, cohort analysis, and revenue impact summary for the current year.',
    format: 'CSV',
    icon: FileSpreadsheet,
    color: 'text-blue-300',
    bg: 'bg-blue-500/10',
  },
  {
    id: 'retention',
    title: 'Retention Campaign Report',
    desc: 'Results of past retention campaigns — customers contacted, responses, recovered revenue, and ROI.',
    format: 'CSV',
    icon: FileText,
    color: 'text-yellow-300',
    bg: 'bg-yellow-500/10',
  },
  {
    id: 'churn',
    title: 'Churn Analysis Report',
    desc: 'In-depth analysis of churned customers: common patterns, feature correlations, and cohort breakdown.',
    format: 'CSV',
    icon: FileSpreadsheet,
    color: 'text-red-300',
    bg: 'bg-red-500/10',
  },
]

const RECENT = [
  { name: 'full_report.csv',      date: '2025-01-15',  size: '245 KB', status: 'Ready' },
  { name: 'risk_report.csv',      date: '2025-01-14',  size: '128 KB', status: 'Ready' },
  { name: 'monthly_report.csv',   date: '2025-01-10',  size: '84 KB',  status: 'Ready' },
  { name: 'accuracy_report.csv',  date: '2025-01-08',  size: '32 KB',  status: 'Ready' },
]

export default function Reports({ setPage }) {
  const [downloading, setDownloading] = useState({})
  const [downloaded, setDownloaded] = useState({})
  const [error, setError] = useState('')

  const download = async (id) => {
    setDownloading((d) => ({ ...d, [id]: true }))
    try {
      setError('')
      const res = await reportsApi.download(id)
      const blob = new Blob([res.data], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `churnshield_${id}_report.csv`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      setDownloaded((d) => ({ ...d, [id]: true }))
      setTimeout(() => setDownloaded((d) => ({ ...d, [id]: false })), 3000)
    } catch (err) {
      setError(err.response?.data?.message || 'Report download failed. Please check live backend and MongoDB connection.')
    } finally {
      setDownloading((d) => ({ ...d, [id]: false }))
    }
  }

  return (
    <div className="space-y-6">
      {error && <div className="red-glow rounded-xl px-4 py-3 text-sm text-red-200">{error}</div>}
      {/* Report cards */}
      <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5">
        {REPORTS.map(({ id, title, desc, format, icon: Icon, color, bg }) => (
          <div key={id} className="glass rounded-2xl p-6 card-3d flex flex-col">
            <div className={`w-14 h-14 rounded-2xl ${bg} flex items-center justify-center mb-5`}>
              <Icon size={28} className={color} />
            </div>
            <h3 className="font-bold text-lg">{title}</h3>
            <p className="text-slate-400 text-sm mt-2 leading-relaxed flex-1">{desc}</p>
            <div className="flex items-center justify-between mt-5">
              <span className="text-xs text-slate-500 bg-white/5 px-2.5 py-1 rounded-lg">
                {format} Format
              </span>
              <button
                onClick={() => download(id)}
                disabled={downloading[id]}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition ${
                  downloaded[id]
                    ? 'green-card text-emerald-300'
                    : 'glow-btn'
                } disabled:opacity-70`}
              >
                {downloading[id] ? (
                  <Loader2 size={15} className="animate-spin" />
                ) : downloaded[id] ? (
                  <CheckCircle size={15} />
                ) : (
                  <Download size={15} />
                )}
                {downloaded[id] ? 'Downloaded!' : `Download ${format}`}
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Recent downloads */}
      <div className="glass rounded-2xl p-6">
        <h3 className="font-bold mb-4">Recent Downloads</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-950/50 text-slate-400 text-xs uppercase">
                <th className="text-left px-4 py-3 rounded-l-lg">File Name</th>
                <th className="text-left px-4 py-3">Generated</th>
                <th className="text-left px-4 py-3">Size</th>
                <th className="text-left px-4 py-3 rounded-r-lg">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {RECENT.map((r) => (
                <tr key={r.name} className="table-row">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <FileSpreadsheet size={15} className="text-emerald-300" />
                      <span className="text-slate-200 font-mono text-xs">{r.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-slate-400">{r.date}</td>
                  <td className="px-4 py-3 text-slate-400">{r.size}</td>
                  <td className="px-4 py-3">
                    <span className="badge bg-emerald-500/15 text-emerald-300 border border-emerald-500/25">
                      {r.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Scheduled reports */}
      <div className="glass rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold">Scheduled Reports</h3>
          <button
            onClick={() => {
              if (setPage) {
                setPage('settings')
              } else {
                alert("Please navigate to Settings > Notifications to schedule reports.")
              }
            }}
            className="glow-btn px-4 py-2 rounded-xl text-sm font-semibold"
          >
            + Schedule
          </button>
        </div>
        <div className="space-y-3">
          {[
            { name: 'Weekly Churn Summary', freq: 'Every Monday 9:00 AM', email: 'admin@churnshield.ai', active: true },
            { name: 'Monthly Full Report',  freq: '1st of each month',    email: 'admin@churnshield.ai', active: true },
          ].map((s) => (
            <div key={s.name} className="flex items-center justify-between bg-white/5 rounded-xl px-4 py-3">
              <div>
                <p className="text-sm font-medium">{s.name}</p>
                <p className="text-xs text-slate-400 mt-0.5">{s.freq} · {s.email}</p>
              </div>
              <span className={`badge ${s.active ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/25' : 'bg-slate-500/15 text-slate-400'}`}>
                {s.active ? 'Active' : 'Paused'}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
