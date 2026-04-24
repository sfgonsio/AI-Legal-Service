/**
 * IntakeButton — top-of-page link into the Intake page with live progress.
 *
 * Replaces the static "0/13" count with a calculated value from
 * /interviews/{id}/progress. Creates an interview on first render if the
 * case has none yet (so the button has something to point to).
 *
 * Mode-appropriate display:
 *   GUIDED_QUESTIONS:  "Intake  5/13"
 *   FREEFORM_NARRATIVE: "Intake  Freeform narrative started"
 *                       "Intake  Narrative complete"
 */
import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { interviewApi } from '../api/client'

export default function IntakeButton({ caseId }) {
  const navigate = useNavigate()
  const [progress, setProgress] = useState(null)
  const [iv, setIv] = useState(null)

  const load = useCallback(async () => {
    try {
      let interview
      try {
        interview = await interviewApi.getForCase(caseId)
      } catch (e) {
        if ((e.message || '').includes('404')) {
          interview = await interviewApi.create(caseId, 'GUIDED_QUESTIONS')
        } else {
          // Non-fatal; keep button visible with unknown state.
          setProgress(null)
          return
        }
      }
      setIv(interview)
      setProgress(await interviewApi.progress(interview.id))
    } catch {
      setProgress(null)
    }
  }, [caseId])

  useEffect(() => { load() }, [load])

  // Light polling while processing so the button reflects completion.
  useEffect(() => {
    if (!iv) return
    if (iv.processing_state !== 'processing') return
    const t = setInterval(load, 1500)
    return () => clearInterval(t)
  }, [iv, load])

  // Re-fetch when the Intake page navigates back (visibility change).
  useEffect(() => {
    const onVis = () => { if (document.visibilityState === 'visible') load() }
    document.addEventListener('visibilitychange', onVis)
    return () => document.removeEventListener('visibilitychange', onVis)
  }, [load])

  let label = 'Intake'
  let sub = '—'
  if (progress) {
    if (progress.mode === 'FREEFORM_NARRATIVE') {
      sub = progress.display
    } else {
      sub = `${progress.answered_count}/${progress.total_count}`
    }
    if (progress.processing_state === 'complete') sub = `${sub} · complete`
    else if (progress.processing_state === 'processing') sub = `${sub} · processing`
    else if (progress.processing_state === 'failed') sub = `${sub} · failed`
  }

  return (
    <button
      onClick={() => navigate(`/case/${caseId}/intake`)}
      className="text-left border border-slate-700 rounded px-3 py-1 bg-slate-800 hover:border-sky-500"
      title="Open Intake Interview"
    >
      <div className="text-xs font-semibold text-slate-100">{label}</div>
      <div className="text-[10px] text-slate-400 font-mono">{sub}</div>
    </button>
  )
}
