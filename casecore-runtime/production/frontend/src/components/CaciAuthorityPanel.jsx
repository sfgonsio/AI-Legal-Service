/**
 * CaciAuthorityPanel
 *
 * Renders the tri-signal authority block (certified / provisional / case decision)
 * and lets an attorney ACCEPT, REJECT, or REPLACE a provisional CACI for a case.
 *
 * Backed by /case-authority/* routes. Never reads provisional records directly.
 */
import { useState } from 'react'
import { caseAuthorityApi } from '../api/client'

function Badge({ label, tone = 'slate' }) {
  const tones = {
    slate: 'bg-slate-700 text-slate-100',
    green: 'bg-emerald-700 text-emerald-50',
    red: 'bg-rose-700 text-rose-50',
    amber: 'bg-amber-700 text-amber-50',
    blue: 'bg-sky-700 text-sky-50',
    gray: 'bg-slate-600 text-slate-200',
  }
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-mono ${tones[tone] || tones.slate}`}>
      {label}
    </span>
  )
}

function toneForGrounding(g) {
  if (g === 'GROUNDED') return 'green'
  if (g === 'GROUNDED_VIA_REPLACEMENT') return 'blue'
  if (g === 'PROPOSED') return 'amber'
  return 'red'
}

export default function CaciAuthorityPanel({
  caseId,
  caciId,
  authority,
  attorneyId = 'unknown',
  role = 'lead_attorney',
  onChange,
}) {
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)
  const [mode, setMode] = useState(null) // 'accept' | 'reject' | 'replace' | null
  const [rationale, setRationale] = useState('')
  const [replAuthorityType, setReplAuthorityType] = useState('STATUTE')
  const [replAuthorityId, setReplAuthorityId] = useState('')
  const [replReason, setReplReason] = useState('')

  if (!authority) return null

  const grounding = authority.effective_grounding
  const badgeTone = toneForGrounding(grounding)
  const state = authority.case_decision?.state || 'PENDING_REVIEW'
  const pinned = authority.pinned_record_id
  const confidence = authority.provisional_candidate?.confidence
  const provStatus = authority.provisional_candidate?.status
  const certifiedPresent = authority.certified?.present

  async function runAction(fn) {
    setBusy(true)
    setErr(null)
    try {
      await fn()
      setMode(null)
      setRationale('')
      setReplAuthorityId('')
      setReplReason('')
      if (onChange) await onChange()
    } catch (e) {
      setErr(e.message || 'action failed')
    } finally {
      setBusy(false)
    }
  }

  const handleAccept = () =>
    runAction(() =>
      caseAuthorityApi.accept(caseId, caciId, pinned, attorneyId, role, rationale || null)
    )

  const handleReject = () => {
    if (!rationale) {
      setErr('Rationale required for REJECT')
      return
    }
    runAction(() =>
      caseAuthorityApi.reject(caseId, caciId, attorneyId, role, rationale)
    )
  }

  const handleReplace = () => {
    if (!replAuthorityId || !replReason) {
      setErr('Replacement authority_id and reason required')
      return
    }
    runAction(() =>
      caseAuthorityApi.replace(
        caseId,
        caciId,
        attorneyId,
        role,
        {
          authority_type: replAuthorityType,
          authority_id: replAuthorityId,
          record_ref: null,
          reason: replReason,
        },
        rationale || replReason
      )
    )
  }

  return (
    <div className="border border-slate-700 rounded-md p-3 bg-slate-800">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="font-mono text-sm text-slate-100">{caciId}</span>
        <Badge label={authority.display_badge || grounding} tone={badgeTone} />
        <Badge label={`decision:${state}`} tone="slate" />
        {certifiedPresent ? (
          <Badge label={`certified:${authority.certified.authority_id}`} tone="green" />
        ) : (
          <Badge label="certified:none" tone="gray" />
        )}
        {provStatus && (
          <Badge
            label={`provisional:${provStatus}${confidence ? ` (${Number(confidence).toFixed(2)})` : ''}`}
            tone={provStatus === 'BLOCKED_UNTRUSTED' ? 'red' : 'amber'}
          />
        )}
      </div>

      <div className="text-xs text-slate-400 mt-2 font-mono break-all">
        decision_id: {authority.decision_id || '—'} · pinned_record_id: {pinned || '—'}
      </div>

      <div className="mt-3 flex gap-2 flex-wrap">
        <button
          disabled={busy || grounding === 'GROUNDED' || provStatus === 'BLOCKED_UNTRUSTED'}
          onClick={() => setMode('accept')}
          className="px-2 py-1 text-xs rounded bg-emerald-700 hover:bg-emerald-600 disabled:bg-slate-600 disabled:cursor-not-allowed"
        >
          Accept
        </button>
        <button
          disabled={busy || state === 'REJECTED'}
          onClick={() => setMode('reject')}
          className="px-2 py-1 text-xs rounded bg-rose-700 hover:bg-rose-600 disabled:bg-slate-600 disabled:cursor-not-allowed"
        >
          Reject
        </button>
        <button
          disabled={busy}
          onClick={() => setMode('replace')}
          className="px-2 py-1 text-xs rounded bg-sky-700 hover:bg-sky-600"
        >
          Replace
        </button>
      </div>

      {mode === 'accept' && (
        <div className="mt-3 space-y-2">
          <div className="text-xs text-slate-400">
            Accepting will pin this case to record_id <code>{pinned || 'none'}</code>.
          </div>
          <textarea
            className="w-full text-xs p-2 rounded bg-slate-900 border border-slate-600"
            placeholder="Optional rationale"
            value={rationale}
            onChange={(e) => setRationale(e.target.value)}
          />
          <div className="flex gap-2">
            <button onClick={handleAccept} disabled={busy} className="px-2 py-1 text-xs rounded bg-emerald-700">
              Confirm Accept
            </button>
            <button onClick={() => setMode(null)} className="px-2 py-1 text-xs rounded bg-slate-700">
              Cancel
            </button>
          </div>
        </div>
      )}

      {mode === 'reject' && (
        <div className="mt-3 space-y-2">
          <textarea
            className="w-full text-xs p-2 rounded bg-slate-900 border border-slate-600"
            placeholder="Rationale (required)"
            value={rationale}
            onChange={(e) => setRationale(e.target.value)}
          />
          <div className="flex gap-2">
            <button onClick={handleReject} disabled={busy} className="px-2 py-1 text-xs rounded bg-rose-700">
              Confirm Reject
            </button>
            <button onClick={() => setMode(null)} className="px-2 py-1 text-xs rounded bg-slate-700">
              Cancel
            </button>
          </div>
        </div>
      )}

      {mode === 'replace' && (
        <div className="mt-3 space-y-2">
          <div className="flex gap-2">
            <select
              value={replAuthorityType}
              onChange={(e) => setReplAuthorityType(e.target.value)}
              className="text-xs p-1 rounded bg-slate-900 border border-slate-600"
            >
              <option value="STATUTE">STATUTE</option>
              <option value="CASE_LAW">CASE_LAW</option>
              <option value="CERTIFIED_CACI">CERTIFIED_CACI</option>
              <option value="CACI">CACI</option>
              <option value="REGULATION">REGULATION</option>
              <option value="OTHER">OTHER</option>
            </select>
            <input
              className="flex-1 text-xs p-1 rounded bg-slate-900 border border-slate-600"
              placeholder="authority_id (e.g. Cal.Civ.Code §1709)"
              value={replAuthorityId}
              onChange={(e) => setReplAuthorityId(e.target.value)}
            />
          </div>
          <input
            className="w-full text-xs p-1 rounded bg-slate-900 border border-slate-600"
            placeholder="Replacement reason (required)"
            value={replReason}
            onChange={(e) => setReplReason(e.target.value)}
          />
          <div className="flex gap-2">
            <button onClick={handleReplace} disabled={busy} className="px-2 py-1 text-xs rounded bg-sky-700">
              Confirm Replace
            </button>
            <button onClick={() => setMode(null)} className="px-2 py-1 text-xs rounded bg-slate-700">
              Cancel
            </button>
          </div>
        </div>
      )}

      {err && <div className="text-rose-400 text-xs mt-2">{err}</div>}
      {authority.error && <div className="text-amber-400 text-xs mt-2">resolver: {authority.error}</div>}
    </div>
  )
}
