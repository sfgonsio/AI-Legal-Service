/**
 * CaseProgressBar
 *
 * Minimal save/progress UI strip. Shows save state, last-saved timestamp,
 * processing status, and review-required count. Offers the four lifecycle
 * actions: Save Draft, Save and Return, Submit for Legal Analysis,
 * Return to Intake.
 *
 * Does not redesign broader UI — this is a single strip component used by
 * the Dashboard and any case-edit view.
 */
import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { caseApi } from '../api/client'

function StateBadge({ state }) {
  const map = {
    DRAFT: 'bg-slate-600 text-slate-100',
    SAVED: 'bg-sky-700 text-sky-50',
    READY_FOR_ANALYSIS: 'bg-indigo-700 text-indigo-50',
    PROCESSING: 'bg-amber-700 text-amber-50 animate-pulse',
    REVIEW_REQUIRED: 'bg-orange-700 text-orange-50',
    APPROVED: 'bg-emerald-700 text-emerald-50',
    RETURNED_TO_INTAKE: 'bg-rose-700 text-rose-50',
  }
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-mono ${map[state] || 'bg-slate-600'}`}>
      {state}
    </span>
  )
}

function fmtTimestamp(ts) {
  if (!ts) return '—'
  try {
    return new Date(ts).toLocaleString()
  } catch {
    return ts
  }
}

export default function CaseProgressBar({ caseId, attorneyId = 'attorney:ui', onChange }) {
  const navigate = useNavigate()
  const [progress, setProgress] = useState(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setErr(null)
    try {
      setProgress(await caseApi.progress(caseId))
    } catch (e) {
      setErr(e.message || 'failed to load progress')
    } finally {
      setLoading(false)
    }
  }, [caseId])

  useEffect(() => {
    load()
  }, [load])

  // Poll while PROCESSING so the UI picks up REVIEW_REQUIRED automatically.
  useEffect(() => {
    if (progress?.save_state !== 'PROCESSING') return
    const timer = setInterval(load, 2000)
    return () => clearInterval(timer)
  }, [progress?.save_state, load])

  async function runAction(fn, msg) {
    setBusy(true)
    setErr(null)
    try {
      await fn()
      await load()
      if (onChange) await onChange()
    } catch (e) {
      setErr((msg ? `${msg}: ` : '') + (e.message || 'failed'))
    } finally {
      setBusy(false)
    }
  }

  if (loading && !progress) return <div className="text-sm text-slate-500">Loading progress…</div>
  if (err && !progress) return <div className="text-sm text-rose-400">{err}</div>
  if (!progress) return null

  const state = progress.save_state
  const canSaveDraft = ['DRAFT', 'SAVED', 'READY_FOR_ANALYSIS'].includes(state)
  const canSaveAndReturn = ['DRAFT', 'SAVED', 'READY_FOR_ANALYSIS'].includes(state)
  const canSubmit = ['SAVED', 'READY_FOR_ANALYSIS'].includes(state)
  const canReturn = ['SAVED', 'READY_FOR_ANALYSIS', 'PROCESSING', 'REVIEW_REQUIRED', 'APPROVED', 'DRAFT'].includes(state)

  return (
    <div className="border border-slate-700 rounded-md p-3 bg-slate-800 space-y-2">
      <div className="flex items-center gap-3 flex-wrap">
        <StateBadge state={state} />
        <span className="text-xs text-slate-400">Last saved: {fmtTimestamp(progress.last_saved_at)}</span>
        {state === 'PROCESSING' && (
          <span className="text-xs text-amber-300">Analyzing — {progress.current_analysis_run?.coa_count ?? 0} COAs…</span>
        )}
        {state === 'REVIEW_REQUIRED' && (
          <button
            onClick={() => navigate(`/case/${caseId}/authority`)}
            className="text-xs px-2 py-0.5 rounded bg-orange-700 hover:bg-orange-600"
          >
            Review {progress.review_required_count} item{progress.review_required_count === 1 ? '' : 's'}
          </button>
        )}
        {progress.last_error_detail && (
          <span className="text-xs text-rose-400 font-mono">err: {progress.last_error_detail}</span>
        )}
      </div>

      <div className="flex gap-2 flex-wrap">
        <button
          disabled={busy || !canSaveDraft}
          onClick={() => runAction(() => caseApi.saveDraft(caseId, { actor_id: attorneyId }), 'save-draft')}
          className="px-2 py-1 text-xs rounded bg-slate-700 hover:bg-slate-600 disabled:opacity-40"
        >
          Save Draft
        </button>
        <button
          disabled={busy || !canSaveAndReturn}
          onClick={async () => {
            await runAction(() => caseApi.saveAndReturn(caseId, { actor_id: attorneyId }), 'save-and-return')
            navigate('/')
          }}
          className="px-2 py-1 text-xs rounded bg-sky-700 hover:bg-sky-600 disabled:opacity-40"
        >
          Save and Return
        </button>
        <button
          disabled={busy || !canSubmit}
          onClick={() => runAction(
            () => caseApi.submitForAnalysis(caseId, attorneyId, 'lead_attorney'),
            'submit-for-analysis'
          )}
          className="px-2 py-1 text-xs rounded bg-emerald-700 hover:bg-emerald-600 disabled:opacity-40"
        >
          Submit for Legal Analysis
        </button>
        <button
          disabled={busy || !canReturn}
          onClick={() => runAction(
            () => caseApi.returnToIntake(caseId, attorneyId, 'attorney requested return'),
            'return-to-intake'
          )}
          className="px-2 py-1 text-xs rounded bg-rose-800 hover:bg-rose-700 disabled:opacity-40"
        >
          Return to Intake
        </button>
      </div>

      {err && <div className="text-xs text-rose-400">{err}</div>}
    </div>
  )
}
