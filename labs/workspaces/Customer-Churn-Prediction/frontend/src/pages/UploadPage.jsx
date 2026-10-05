import { useRef, useState } from 'react'
import {
  AlertCircle,
  CheckCircle,
  CloudUpload,
  Database,
  FileCheck,
  Loader2,
  Play,
  XCircle,
} from 'lucide-react'
import { uploadApi } from '../services/api.js'

const REQUIRED_COLS = [
  'Customer ID',
  'Age',
  'Gender',
  'Location',
  'Total Orders',
  'Last Purchase Date',
  'Average Order Value',
  'Cart Abandonment Rate (%)',
  'Website Visits',
  'Customer Rating',
  'Payment Method',
  'Return Count',
  'Support Tickets',
  'Churn Status',
]

const MAX_FILE_SIZE = 1024 * 1024 * 1024

function getErrorMessage(err) {
  if (err.code === 'ECONNABORTED') {
    return 'Upload is still taking too long. The frontend now waits up to 10 minutes; check MongoDB Atlas connection, IP whitelist, and backend terminal logs.'
  }
  if (!err.response) {
    return 'Backend not reachable. Start Flask backend and check VITE_API_BASE_URL in frontend .env.'
  }
  const data = err.response.data || {}
  if (data.missing_columns?.length) {
    return `Dataset validation failed. Missing columns: ${data.missing_columns.join(', ')}`
  }
  return data.message || 'Upload failed. Please check backend terminal error and MongoDB connection.'
}

export default function UploadPage({ setPage }) {
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [missingCols, setMissingCols] = useState([])
  const inputRef = useRef(null)

  const pickFile = (selectedFile) => {
    if (!selectedFile) return

    const fileName = selectedFile.name.toLowerCase()
    const validType = ['.csv', '.xlsx', '.xls'].some((ext) => fileName.endsWith(ext))

    if (!validType) {
      setStatus({ type: 'error', message: 'Only CSV or Excel files are supported.' })
      setMissingCols([])
      return
    }

    if (selectedFile.size > MAX_FILE_SIZE) {
      setStatus({ type: 'error', message: 'File size must be less than 1GB.' })
      setMissingCols([])
      return
    }

    setFile(selectedFile)
    setProgress(0)
    setStatus(null)
    setMissingCols([])
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    pickFile(e.dataTransfer.files?.[0])
  }

  const buildFormData = () => {
    const fd = new FormData()
    fd.append('file', file)
    return fd
  }

  const handleValidate = async () => {
    if (!file) {
      setStatus({ type: 'error', message: 'Please select a file first.' })
      return
    }

    setLoading(true)
    setStatus(null)
    setProgress(0)
    setMissingCols([])

    try {
      const res = await uploadApi.validate(buildFormData())
      setStatus({ type: 'success', message: res.data.message || 'Dataset validation successful.' })
      setMissingCols([])
    } catch (err) {
      const data = err.response?.data || {}
      if (data.missing_columns?.length) {
        setMissingCols(data.missing_columns)
      }
      setStatus({ type: 'error', message: getErrorMessage(err) })
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setStatus({ type: 'error', message: 'Please select a file first.' })
      return
    }

    setLoading(true)
    setStatus(null)
    setProgress(0)
    setMissingCols([])

    try {
      const res = await uploadApi.upload(buildFormData(), (event) => {
        if (!event.total) return
        setProgress(Math.round((event.loaded * 100) / event.total))
      })
      setStatus({ type: 'success', message: res.data.message || 'Dataset uploaded successfully.' })
      setProgress(100)
      setMissingCols([])
    } catch (err) {
      const data = err.response?.data || {}
      if (data.missing_columns?.length) {
        setMissingCols(data.missing_columns)
      }
      setStatus({ type: 'error', message: getErrorMessage(err) })
    } finally {
      setLoading(false)
    }
  }

  const downloadSample = () => {
    window.open(uploadApi.downloadSample(), '_blank', 'noopener,noreferrer')
  }

  const startPrediction = () => {
    if (setPage) {
      setPage('predict')
      return
    }
    setStatus({ type: 'success', message: 'Dataset ready. Open Churn Prediction page from sidebar.' })
  }

  return (
    <div className="space-y-6">
      <div className="glass rounded-2xl p-8">
        <h2 className="text-xl font-bold">Dataset Upload</h2>
        <p className="text-slate-400 mt-1 mb-6">
          Upload your customer dataset (CSV or Excel) to start churn prediction
        </p>

        <div
          className={`border-2 border-dashed rounded-2xl min-h-56 flex flex-col items-center justify-center cursor-pointer transition-all p-6 ${
            dragging
              ? 'border-indigo-400 bg-indigo-500/10'
              : 'border-indigo-400/40 hover:border-indigo-400/80 hover:bg-indigo-500/5'
          }`}
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
        >
          <CloudUpload size={52} className="text-indigo-300 mb-4" />
          <p className="text-lg font-medium text-center">
            Drag & Drop your file here or <span className="text-cyan-300 underline">browse</span>
          </p>
          <p className="text-sm text-slate-400 mt-2">Supports CSV, Excel (.xlsx, .xls) • Max 1GB • CSV uploads are processed in fast chunks</p>

          {file && (
            <div className="mt-3 flex flex-wrap items-center justify-center gap-2 text-emerald-300 text-sm">
              <CheckCircle size={16} />
              <span>Selected:</span>
              <strong>{file.name}</strong>
              <span>({(file.size / 1024).toFixed(1)} KB)</span>
            </div>
          )}

          {loading && progress > 0 && (
            <div className="mt-5 w-full max-w-md">
              <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                <div className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-cyan-400" style={{ width: `${progress}%` }} />
              </div>
              <p className="text-xs text-slate-400 mt-2 text-center">Uploading {progress}%</p>
            </div>
          )}

          <input
            ref={inputRef}
            type="file"
            className="hidden"
            accept=".csv,.xlsx,.xls"
            onChange={(e) => pickFile(e.target.files?.[0])}
          />
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
          <ActionBtn icon={Database} label="Sample Dataset" onClick={downloadSample} disabled={loading} />
          <ActionBtn icon={FileCheck} label="Validate" onClick={handleValidate} loading={loading} disabled={loading || !file} />
          <ActionBtn icon={CloudUpload} label="Upload Dataset" onClick={handleUpload} primary loading={loading} disabled={loading || !file} />
          <ActionBtn icon={Play} label="Start Prediction" onClick={startPrediction} green disabled={loading} />
        </div>

        {loading && (
          <div className="mt-5 flex items-center gap-3 text-cyan-300">
            <Loader2 size={18} className="animate-spin" />
            <span>Processing dataset with fast backend chunk upload. Please wait…</span>
          </div>
        )}

        {status && !loading && (
          <div
            className={`mt-5 flex items-start gap-3 rounded-xl px-4 py-3 border ${
              status.type === 'success'
                ? 'bg-emerald-500/10 border-emerald-400/30 text-emerald-200'
                : 'bg-red-500/10 border-red-400/30 text-red-200'
            }`}
          >
            {status.type === 'success' ? (
              <CheckCircle size={18} className="shrink-0 mt-0.5" />
            ) : (
              <XCircle size={18} className="shrink-0 mt-0.5" />
            )}
            <span className="text-sm font-medium">{status.message}</span>
          </div>
        )}
      </div>

      <div className="glass rounded-2xl p-6">
        <h3 className="font-bold mb-2 flex items-center gap-2">
          <FileCheck size={18} className="text-cyan-300" />
          Required Columns
        </h3>
        <p className="text-xs text-slate-400 mb-4">
          Your uploaded CSV or Excel file must contain these exact column headers. If any required columns are missing, they will be highlighted below.
        </p>
        <div className="flex flex-wrap gap-2">
          {REQUIRED_COLS.map((col) => {
            const isMissing = missingCols.includes(col)
            return (
              <span
                key={col}
                className={`px-3 py-2 rounded-lg border text-xs transition-all duration-300 ${
                  isMissing
                    ? 'bg-red-500/20 border-red-500 text-red-200 animate-pulse font-bold'
                    : 'bg-slate-900 border-white/10 text-slate-300'
                }`}
              >
                {col} {isMissing && '❌'}
              </span>
            )
          })}
        </div>
      </div>

      <div className="glass rounded-2xl p-6">
        <h3 className="font-bold mb-4 flex items-center gap-2">
          <AlertCircle size={18} className="text-cyan-300" />
          Dataset Guidelines
        </h3>
        <ul className="space-y-2 text-sm text-slate-300">
          {[
            'Each row represents one unique customer.',
            'Customer ID must be unique for every customer.',
            'Churn Status column must be 0 (retained) or 1 (churned).',
            'Last Purchase Date should be in YYYY-MM-DD format.',
            'Cart Abandonment Rate (%) should be between 0–100.',
            'Customer Rating should be on a 1–5 scale.',
          ].map((tip) => (
            <li key={tip} className="flex items-start gap-2">
              <span className="text-cyan-300 shrink-0">•</span>
              {tip}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

function ActionBtn({ icon: Icon, label, onClick, primary, green, loading, disabled }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled || loading}
      className={`${
        green ? 'green-glow' : primary ? 'glow-btn' : 'glass hover:bg-white/10'
      } rounded-xl p-4 flex items-center justify-center gap-2 text-sm font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed`}
    >
      {loading ? <Loader2 size={16} className="animate-spin" /> : <Icon size={16} />}
      {label}
    </button>
  )
}
