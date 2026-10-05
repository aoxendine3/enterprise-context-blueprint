// src/pages/Performance.jsx

import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { performanceApi } from '../services/api.js'

const EMPTY = {
  accuracy: 0,
  precision: 0,
  recall: 0,
  f1_score: 0,
  roc_auc: 0,
  confusion_matrix: {
    true_negative: 0,
    false_positive: 0,
    false_negative: 0,
    true_positive: 0,
  },
  feature_importance: [],
  roc_curve: [],
  training_history: [],
  model_info: {
    type: 'XGBoost Classifier',
    version: '',
    trained_on: '',
    training_samples: 0,
  },
}

const METRICS = [
  {
    key: 'accuracy',
    label: 'Accuracy',
    color: 'text-cyan-300',
  },
  {
    key: 'precision',
    label: 'Precision',
    color: 'text-emerald-300',
  },
  {
    key: 'recall',
    label: 'Recall',
    color: 'text-indigo-300',
  },
  {
    key: 'f1_score',
    label: 'F1 Score',
    color: 'text-purple-300',
  },
  {
    key: 'roc_auc',
    label: 'ROC AUC',
    color: 'text-amber-300',
  },
]

function safePercent(value) {
  const num = Number(value)
  if (Number.isNaN(num)) return 0
  return Math.max(0, Math.min(100, num))
}

export default function Performance() {
  const [data, setData] = useState(EMPTY)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let mounted = true

    performanceApi
      .get()
      .then((res) => {
        if (!mounted) return

        const apiData = res?.data || EMPTY

        setData({
          ...EMPTY,
          ...apiData,
          confusion_matrix: {
            ...EMPTY.confusion_matrix,
            ...(apiData.confusion_matrix || {}),
          },
          model_info: {
            ...EMPTY.model_info,
            ...(apiData.model_info || {}),
          },
          feature_importance: Array.isArray(apiData.feature_importance)
            ? apiData.feature_importance
            : [],
          roc_curve: Array.isArray(apiData.roc_curve)
            ? apiData.roc_curve
            : [],
          training_history: Array.isArray(apiData.training_history)
            ? apiData.training_history
            : [],
        })
      })
      .catch((err) => {
        if (!mounted) return

        setError(
          err?.response?.data?.message ||
            err?.response?.data?.error ||
            'Unable to load live model performance data.'
        )
        setData(EMPTY)
      })
      .finally(() => {
        if (mounted) setLoading(false)
      })

    return () => {
      mounted = false
    }
  }, [])

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 size={36} className="animate-spin text-cyan-300" />
      </div>
    )
  }

  const d = data || EMPTY
  const cm = d.confusion_matrix || EMPTY.confusion_matrix
  const featureImportance = d.feature_importance || []
  const rocCurve = d.roc_curve || []
  const modelInfo = d.model_info || EMPTY.model_info

  return (
    <div className="space-y-6">
      {error && (
        <div className="red-glow rounded-xl px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      {/* Metric badges */}
      <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-5 gap-4">
        {METRICS.map(({ key, label, color }) => {
          const value = safePercent(d[key])

          return (
            <div key={key} className="glass rounded-2xl p-5">
              <p className="text-slate-400 text-xs mb-2">{label}</p>

              <h3 className={`text-3xl font-bold ${color}`}>
                {value.toFixed(1)}%
              </h3>

              <div className="mt-3 h-1.5 rounded-full bg-white/10 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-indigo-500"
                  style={{ width: `${value}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>

      {/* Charts row */}
      <div className="grid lg:grid-cols-3 gap-5">
        {/* Confusion matrix */}
        <div className="glass rounded-2xl p-5">
          <h3 className="font-bold mb-5">Confusion Matrix</h3>

          <div className="grid grid-cols-2 gap-2 max-w-xs mx-auto text-center">
            <MatCell
              label="True Negative"
              value={cm.true_negative}
              color="bg-emerald-500/20 border-emerald-500/30"
            />

            <MatCell
              label="False Positive"
              value={cm.false_positive}
              color="bg-red-500/20 border-red-500/30"
            />

            <MatCell
              label="False Negative"
              value={cm.false_negative}
              color="bg-red-500/20 border-red-500/30"
            />

            <MatCell
              label="True Positive"
              value={cm.true_positive}
              color="bg-emerald-500/20 border-emerald-500/30"
            />
          </div>

          <div className="flex justify-around text-xs text-slate-500 mt-3">
            <span>Pred: Non-Churn</span>
            <span>Pred: Churn</span>
          </div>
        </div>

        {/* Feature importance */}
        <div className="glass rounded-2xl p-5">
          <h3 className="font-bold mb-4">Feature Importance</h3>

          {featureImportance.length === 0 ? (
            <EmptyChartText text="No feature importance data available." />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={featureImportance} layout="vertical">
                <XAxis type="number" hide />

                <YAxis
                  type="category"
                  dataKey="feature"
                  width={150}
                  tick={{ fontSize: 10, fill: '#94a3b8' }}
                />

                <Tooltip
                  contentStyle={{
                    background: '#0c1427',
                    border: 'none',
                    borderRadius: 8,
                    fontSize: 11,
                  }}
                  itemStyle={{ color: '#ffffff' }}
                  labelStyle={{ color: '#94a3b8' }}
                  formatter={(v) => [`${Number(v).toFixed(1)}%`, 'Importance']}
                />

                <Bar dataKey="score" radius={[0, 6, 6, 0]}>
                  {featureImportance.map((_, i) => (
                    <Cell
                      key={`feature-cell-${i}`}
                      fill={`hsl(${220 - i * 15}, 80%, ${65 - i * 3}%)`}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* ROC curve */}
        <div className="glass rounded-2xl p-5">
          <h3 className="font-bold mb-1">ROC Curve</h3>
          <p className="text-xs text-slate-400 mb-4">
            AUC = {safePercent(d.roc_auc).toFixed(1)}%
          </p>

          {rocCurve.length === 0 ? (
            <EmptyChartText text="No ROC curve data available." />
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={rocCurve}>
                <XAxis
                  dataKey="fpr"
                  label={{
                    value: 'FPR %',
                    position: 'insideBottom',
                    offset: -4,
                    fontSize: 10,
                    fill: '#64748b',
                  }}
                  tick={{ fontSize: 10, fill: '#94a3b8' }}
                />

                <YAxis
                  dataKey="tpr"
                  label={{
                    value: 'TPR %',
                    angle: -90,
                    position: 'insideLeft',
                    fontSize: 10,
                    fill: '#64748b',
                  }}
                  tick={{ fontSize: 10, fill: '#94a3b8' }}
                />

                <Tooltip
                  contentStyle={{
                    background: '#0c1427',
                    border: 'none',
                    borderRadius: 8,
                    fontSize: 11,
                  }}
                  itemStyle={{ color: '#ffffff' }}
                  labelStyle={{ color: '#94a3b8' }}
                  formatter={(v) => [`${Number(v).toFixed(1)}%`, '']}
                />

                <Line
                  type="monotone"
                  dataKey="tpr"
                  stroke="#19c37d"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#19c37d' }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Model info */}
      <div className="glass rounded-2xl p-6">
        <h3 className="font-bold mb-4">Model Information</h3>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            ['Model Type', modelInfo.type || 'XGBoost Classifier'],
            ['XGBoost Version', modelInfo.version || 'Not available'],
            ['Last Trained', modelInfo.trained_on || 'Not available'],
            [
              'Training Samples',
              Number(modelInfo.training_samples || 0).toLocaleString(),
            ],
          ].map(([label, val]) => (
            <div key={label}>
              <p className="text-slate-400 text-xs">{label}</p>
              <p className="text-white font-semibold mt-1">{val}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function MatCell({ label, value, color }) {
  const safeValue = Number(value || 0)

  return (
    <div className={`rounded-xl p-4 border ${color}`}>
      <div className="text-2xl font-bold">{safeValue.toLocaleString()}</div>
      <div className="text-xs text-slate-400 mt-1">{label}</div>
    </div>
  )
}

function EmptyChartText({ text }) {
  return (
    <div className="h-[240px] flex items-center justify-center text-sm text-slate-400 text-center">
      {text}
    </div>
  )
}