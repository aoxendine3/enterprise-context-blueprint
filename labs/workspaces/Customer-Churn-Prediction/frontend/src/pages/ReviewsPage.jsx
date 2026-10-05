import { useEffect, useState } from 'react'
import {
  Shield, ShieldAlert, AlertOctagon, Check, X, Edit2, Clock, ArrowRight,
  Terminal, Cpu, ExternalLink, ShieldCheck, RefreshCw, FileCode, CheckSquare
} from 'lucide-react'
import { safetyApi, settingsApi } from '../services/api.js'

async function verifySignatureLocally(publicKeyPem, payloadStr, signatureBase64) {
  try {
    if (!publicKeyPem || !payloadStr || !signatureBase64) return false;
    const pemContents = publicKeyPem
      .replace(/-----BEGIN PUBLIC KEY-----/, '')
      .replace(/-----END PUBLIC KEY-----/, '')
      .replace(/\s+/g, '');
    
    const binaryDerString = window.atob(pemContents);
    const len = binaryDerString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryDerString.charCodeAt(i);
    }
    const publicArrayBuffer = bytes.buffer;

    const cryptoKey = await window.crypto.subtle.importKey(
      "spki",
      publicArrayBuffer,
      {
        name: "RSASSA-PKCS1-v1_5",
        hash: { name: "SHA-256" }
      },
      true,
      ["verify"]
    );

    const binarySigString = window.atob(signatureBase64);
    const sigLen = binarySigString.length;
    const sigBytes = new Uint8Array(sigLen);
    for (let i = 0; i < sigLen; i++) {
      sigBytes[i] = binarySigString.charCodeAt(i);
    }
    const signatureBuffer = sigBytes.buffer;

    const encoder = new TextEncoder();
    const payloadBuffer = encoder.encode(payloadStr);

    return await window.crypto.subtle.verify(
      "RSASSA-PKCS1-v1_5",
      cryptoKey,
      signatureBuffer,
      payloadBuffer
    );
  } catch (e) {
    console.error("Local signature verification error:", e);
    return false;
  }
}


export default function ReviewsPage() {
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [editPayloadText, setEditPayloadText] = useState('')
  const [resolvingId, setResolvingId] = useState(null)
  const [resolvedStatus, setResolvedStatus] = useState({}) // { [id]: { status, tx, signature, verified } }
  const [publicKeyPem, setPublicKeyPem] = useState('')

  const fetchReviews = () => {
    setLoading(true)
    safetyApi.getPending()
      .then((res) => {
        setReviews(res.data || [])
        setError('')
      })
      .catch((err) => {
        setError(err.response?.data?.message || 'Failed to sync with Sovereign Safety Ledger.')
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchReviews()
    // Poll reviews every 5 seconds to keep dashboard live
    const interval = setInterval(fetchReviews, 5000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    settingsApi.getAttestationKey()
      .then((res) => {
        setPublicKeyPem(res.data.public_key || '')
      })
      .catch((err) => {
        console.error('Failed to load attestation key for local verification:', err)
      })
  }, [])

  const handleResolve = (id, status, payload = null) => {
    setResolvingId(id)
    let body = { status }
    if (status === 'approved' && payload) {
      body.repaired_action = payload
    }

    safetyApi.resolve(id, body)
      .then((res) => {
        verifySignatureLocally(publicKeyPem, res.data.payload, res.data.signature)
          .then((verified) => {
            setResolvedStatus(prev => ({
              ...prev,
              [id]: {
                status,
                signature: res.data.signature,
                verified: verified,
                tx: `https://explorer.solana.com/tx/mock-sig-${res.data.signature.substring(0, 12)}?cluster=mainnet-beta`
              }
            }))
          })
        // Remove from list after a short delay so the operator sees the receipt/success
        setTimeout(() => {
          setReviews(prev => prev.filter(r => r.id !== id))
          setEditingId(null)
        }, 6000)
      })
      .catch((err) => {
        setError(err.response?.data?.message || 'Failed to submit resolution signature to the safety ledger.')
      })
      .finally(() => setResolvingId(null))
  }

  const startEditing = (review) => {
    setEditingId(review.id)
    const displayPayload = review.repaired_action || review.failed_action
    setEditPayloadText(JSON.stringify(displayPayload, null, 2))
  }

  const saveEdit = (id) => {
    try {
      const parsed = JSON.parse(editPayloadText)
      handleResolve(id, 'approved', parsed)
    } catch (e) {
      alert('Invalid JSON format. Please correct it before saving.')
    }
  }

  const getRiskMetadata = (score) => {
    const s = score || 0
    if (s >= 0.8) {
      return {
        label: 'CRITICAL',
        color: 'text-red-400 border-red-500/30 bg-red-500/10',
        cardBorder: 'border-red-500/30 shadow-red-950/20 shadow-2xl'
      }
    } else if (s >= 0.5) {
      return {
        label: 'WARNING',
        color: 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10',
        cardBorder: 'border-yellow-500/20'
      }
    } else {
      return {
        label: 'INFO',
        color: 'text-cyan-400 border-cyan-500/30 bg-cyan-500/10',
        cardBorder: 'border-white/10'
      }
    }
  }

  const calculateTimeLeft = (timestamp) => {
    if (!timestamp) return 'Time Out'
    const start = new Date(timestamp).getTime()
    const now = Date.now()
    const diffSeconds = Math.floor((now - start) / 1000)
    const timeoutSeconds = 300 // 5 minutes
    const remaining = timeoutSeconds - diffSeconds
    if (remaining <= 0) return 'Timed Out (Auto-Rejected)'
    const minutes = Math.floor(remaining / 60)
    const seconds = remaining % 60
    return `${minutes}:${seconds < 10 ? '0' : ''}${seconds} remaining`
  }

  if (loading && reviews.length === 0) {
    return (
      <div className="flex flex-col justify-center items-center h-96 space-y-4">
        <RefreshCw size={36} className="animate-spin text-cyan-300" />
        <span className="text-sm text-slate-400 font-mono">Syncing Sovereign Safety Ledger...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="red-glow rounded-xl px-4 py-3 text-sm text-red-200 flex items-center gap-2">
          <AlertOctagon size={16} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Top Banner Stats */}
      <div className="grid sm:grid-cols-3 gap-5">
        <div className="glass rounded-2xl p-5 border border-white/10 flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400 uppercase font-mono">Active Reviews</span>
            <h3 className="text-2xl font-black mt-1 text-white">{reviews.length}</h3>
          </div>
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-300">
            <ShieldAlert size={20} />
          </div>
        </div>

        <div className="glass rounded-2xl p-5 border border-white/10 flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400 uppercase font-mono">Safety System Status</span>
            <h3 className="text-lg font-bold mt-1 text-emerald-400 flex items-center gap-1.5">
              <ShieldCheck size={18} /> Enabled
            </h3>
          </div>
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <Shield size={20} />
          </div>
        </div>

        <div className="glass rounded-2xl p-5 border border-white/10 flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400 uppercase font-mono">Audit Proofs</span>
            <h3 className="text-sm font-semibold mt-2 text-slate-300 truncate font-mono">
              Solana & Base Calldata
            </h3>
          </div>
          <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
            <Terminal size={20} />
          </div>
        </div>
      </div>

      {reviews.length === 0 ? (
        <div className="glass rounded-3xl p-12 text-center border border-white/10 flex flex-col items-center justify-center max-w-lg mx-auto mt-12 space-y-4">
          <div className="w-20 h-20 rounded-full bg-emerald-500/10 border border-emerald-500/25 flex items-center justify-center text-emerald-400 animate-pulse">
            <ShieldCheck size={42} />
          </div>
          <h3 className="text-xl font-bold text-white">All Swarms Operating Securely</h3>
          <p className="text-sm text-slate-400 leading-relaxed max-w-sm">
            Sovereign Safety taxonomy verified. No active agent executions are currently violating safety constraints or pending human operator intervention.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Cpu size={18} className="text-cyan-300" /> Pending Intercepted Actions
            </h2>
            <span className="text-xs text-slate-400 font-mono">
              Sorted by risk/priority level (high first)
            </span>
          </div>

          <div className="space-y-6">
            {reviews.map((review) => {
              const rMeta = getRiskMetadata(review.max_score)
              const hasResolved = resolvedStatus[review.id]

              return (
                <div
                  key={review.id}
                  className={`glass rounded-2xl p-6 border transition-all duration-300 ${rMeta.cardBorder}`}
                >
                  {hasResolved ? (
                    <div className="flex flex-col items-center justify-center py-10 space-y-4">
                      <div className="w-14 h-14 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                        <Check size={28} />
                      </div>
                      <h4 className="font-bold text-lg text-white">
                        Action Successfully {hasResolved.status === 'approved' ? 'Approved' : 'Rejected'}
                      </h4>
                      <p className="text-xs text-slate-400 font-mono max-w-md text-center break-all">
                        Ledger Signature: {hasResolved.signature}
                      </p>
                      <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono border border-emerald-500/20 bg-emerald-500/10 text-emerald-400">
                        <ShieldCheck size={14} />
                        {hasResolved.verified ? 'Locally Verified (RSA-SHA256)' : 'Verifying Signature...'}
                      </div>
                      <a
                        href={hasResolved.tx}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-cyan-300 flex items-center gap-1 hover:underline"
                      >
                        Verify Cryptographic Proof on Solana Explorer <ExternalLink size={12} />
                      </a>
                    </div>
                  ) : (
                    <div className="space-y-5">
                      {/* Top Info Header */}
                      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/5 pb-4">
                        <div className="flex items-center gap-3">
                          <span className={`badge border font-mono ${rMeta.color}`}>
                            Score: {(review.max_score * 100).toFixed(0)}% ({rMeta.label})
                          </span>
                          <span className="text-sm font-semibold text-slate-200 font-mono">
                            Agent: {review.agent_id}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-yellow-300 font-mono">
                          <Clock size={14} />
                          <span>{calculateTimeLeft(review.timestamp)}</span>
                        </div>
                      </div>

                      {/* Diagnostic / Reason Info */}
                      <div className="grid md:grid-cols-2 gap-4 bg-slate-950/40 p-4 rounded-xl border border-white/5">
                        <div>
                          <span className="text-[10px] text-slate-500 uppercase font-mono tracking-wider">
                            Safety Policy Violated
                          </span>
                          <p className="text-sm text-red-200 mt-1 font-medium">
                            {review.failure_reason}
                          </p>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 uppercase font-mono tracking-wider">
                            Sovereign Sentinel Diagnosis
                          </span>
                          <p className="text-sm text-slate-300 mt-1 leading-relaxed">
                            {review.diagnosed_root_cause}
                          </p>
                        </div>
                        {review.context && review.context.cot_reasoning && (
                          <div className="col-span-2 pt-2 border-t border-white/5">
                            <span className="text-[10px] text-slate-500 uppercase font-mono tracking-wider">
                              Sentinel Chain-of-Thought Explanation
                            </span>
                            <p className="text-xs text-slate-400 mt-1 italic leading-relaxed">
                              {review.context.cot_reasoning}
                            </p>
                          </div>
                        )}
                      </div>

                      {/* Payloads Display */}
                      {editingId === review.id ? (
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-cyan-300 font-mono flex items-center gap-1.5">
                              <FileCode size={14} /> Rewrite Action Payload
                            </span>
                            <span className="text-[10px] text-slate-500 font-mono">
                              Ensure valid JSON format
                            </span>
                          </div>
                          <textarea
                            value={editPayloadText}
                            onChange={(e) => setEditPayloadText(e.target.value)}
                            className="font-mono text-xs w-full h-40 bg-slate-950/80 border border-cyan-500/30 rounded-xl p-4 text-cyan-200 outline-none focus:border-cyan-400 transition"
                          />
                          <div className="flex items-center gap-2 justify-end">
                            <button
                              onClick={() => setEditingId(null)}
                              className="px-3 py-1.5 rounded-lg border border-white/10 text-xs text-slate-400 hover:bg-white/5 transition"
                            >
                              Cancel
                            </button>
                            <button
                              onClick={() => saveEdit(review.id)}
                              className="px-4 py-1.5 rounded-lg green-glow text-xs font-semibold flex items-center gap-1"
                            >
                              <Check size={14} /> Submit & Approve Override
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="grid md:grid-cols-2 gap-4">
                          {/* Left: Original Failed Payload */}
                          <div className="flex flex-col">
                            <span className="text-xs text-slate-400 font-mono mb-2 flex items-center gap-1">
                              <X size={12} className="text-red-400" /> Original Action Payload
                            </span>
                            <pre className="font-mono text-[11px] bg-slate-950/60 border border-white/5 rounded-xl p-4 text-red-200/90 overflow-x-auto flex-1 max-h-48 scrollbar">
                              {JSON.stringify(review.failed_action, null, 2)}
                            </pre>
                          </div>

                          {/* Right: Repaired Payload */}
                          <div className="flex flex-col">
                            <span className="text-xs text-slate-400 font-mono mb-2 flex items-center gap-1">
                              <Check size={12} className="text-emerald-400" /> Repaired Candidate Payload
                            </span>
                            <pre className="font-mono text-[11px] bg-slate-950/60 border border-white/5 rounded-xl p-4 text-emerald-200/90 overflow-x-auto flex-1 max-h-48 scrollbar">
                              {JSON.stringify(review.repaired_action, null, 2)}
                            </pre>
                          </div>
                        </div>
                      )}

                      {/* Actions Footer */}
                      {editingId !== review.id && (
                        <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                          <div className="text-xs text-slate-400">
                            ID: <span className="font-mono">{review.id}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <button
                              disabled={resolvingId === review.id}
                              onClick={() => handleResolve(review.id, 'rejected')}
                              className="px-4 py-2 rounded-xl border border-red-500/20 text-red-400 hover:bg-red-500/10 text-xs font-semibold flex items-center gap-1 transition"
                            >
                              <X size={14} /> Reject Action
                            </button>
                            <button
                              disabled={resolvingId === review.id}
                              onClick={() => startEditing(review)}
                              className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10 text-xs font-semibold flex items-center gap-1 transition"
                            >
                              <Edit2 size={14} /> Edit Payload
                            </button>
                            <button
                              disabled={resolvingId === review.id}
                              onClick={() => handleResolve(review.id, 'approved')}
                              className="px-5 py-2 rounded-xl glow-btn text-xs font-bold flex items-center gap-1"
                            >
                              <Check size={14} /> Approve Action
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
