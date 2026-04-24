/**
 * CaseIntake — Intake Interview page.
 *
 * Two modes:
 *   GUIDED_QUESTIONS  — user answers a preset set of questions one at a time
 *   FREEFORM_NARRATIVE — user pastes/types one narrative block
 *
 * Users can switch between modes without losing data (answers + narrative
 * persist across switches). Completion is explicit — a dedicated button —
 * and only then does the server run actor extraction.
 */
import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { interviewApi } from '../api/client'

function Badge({ children, tone = 'slate' }) {
  const map = {
    slate: 'bg-slate-700 text-slate-100',
    sky: 'bg-sky-700 text-sky-50',
    amber: 'bg-amber-700 text-amber-50',
    emerald: 'bg-emerald-700 text-emerald-50',
    rose: 'bg-rose-700 text-rose-50',
  }
  return <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${map[tone]}`}>{children}</span>
}

function stateTone(s) {
  if (s === 'complete') return 'emerald'
  if (s === 'processing') return 'amber'
  if (s === 'failed') return 'rose'
  if (s === 'actors_identified') return 'emerald'
  if (s === 'saved') return 'sky'
  return 'slate'
}

export default function CaseIntake() {
  const { id: caseId } = useParams()
  const [interview, setInterview] = useState(null)
  const [progress, setProgress] = useState(null)
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  const [saveIndicator, setSaveIndicator] = useState('')

  const load = useCallback(async () => {
    try {
      setErr(null)
      let iv
      try {
        iv = await interviewApi.getForCase(caseId)
      } catch (e) {
        if ((e.message || '').includes('404')) {
          iv = await interviewApi.create(caseId, 'GUIDED_QUESTIONS')
        } else {
          throw e
        }
      }
      setInterview(iv)
      setProgress(await interviewApi.progress(iv.id))
    } catch (e) {
      setErr(e.message || 'failed to load interview')
    }
  }, [caseId])

  useEffect(() => { load() }, [load])

  // Poll while processing, so we show completion/actors extracted.
  useEffect(() => {
    if (!interview) return
    if (interview.processing_state !== 'processing') return
    const t = setInterval(load, 1500)
    return () => clearInterval(t)
  }, [interview, load])

  async function onSwitchMode(mode) {
    if (!interview) return
    if (interview.mode === mode) return
    setBusy(true); setErr(null)
    try {
      const iv = await interviewApi.switchMode(interview.id, mode)
      setInterview(iv)
      setProgress(await interviewApi.progress(iv.id))
    } catch (e) { setErr(e.message || 'mode switch failed') }
    finally { setBusy(false) }
  }

  async function onAnswerChange(questionId, text) {
    // optimistic update
    setInterview((prev) => prev && ({
      ...prev,
      questions: prev.questions.map((q) => q.id === questionId ? { ...q, answer_text: text } : q),
    }))
    setSaveIndicator('saving…')
    try {
      const q = await interviewApi.updateQuestion(questionId, text)
      setInterview((prev) => prev && ({
        ...prev,
        questions: prev.questions.map((x) => x.id === q.id ? { ...x, ...q } : x),
      }))
      setProgress(await interviewApi.progress(interview.id))
      setSaveIndicator('saved')
      setTimeout(() => setSaveIndicator(''), 1200)
    } catch (e) {
      setSaveIndicator('save failed')
      setErr(e.message || 'save failed')
    }
  }

  async function onNarrativeChange(text) {
    setInterview((prev) => prev && ({ ...prev, narrative_text: text }))
    setSaveIndicator('saving…')
    try {
      const iv = await interviewApi.updateNarrative(interview.id, text)
      setInterview(iv)
      setProgress(await interviewApi.progress(iv.id))
      setSaveIndicator('saved')
      setTimeout(() => setSaveIndicator(''), 1200)
    } catch (e) {
      setSaveIndicator('save failed')
      setErr(e.message || 'save failed')
    }
  }

  async function onComplete() {
    if (!interview) return
    if (!confirm('Mark interview complete? This triggers actor extraction but does not start legal analysis.')) return
    setBusy(true); setErr(null)
    try {
      const iv = await interviewApi.complete(interview.id)
      setInterview(iv)
      setProgress(await interviewApi.progress(iv.id))
    } catch (e) {
      setErr(e.message || 'complete failed')
    } finally {
      setBusy(false)
    }
  }

  if (err && !interview) return <div className="p-6 text-rose-400">{err}</div>
  if (!interview) return <div className="p-6 text-slate-400">Loading intake…</div>

  const terminal = interview.processing_state === 'complete'
  const locked = interview.processing_state === 'processing' || terminal

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Case Intake — Case #{caseId}</h1>
        <Link to={`/case/${caseId}`} className="text-sm text-sky-400 hover:underline">← back to case</Link>
      </div>

      <div className="border border-slate-700 rounded-md p-3 bg-slate-800 space-y-2">
        <div className="flex items-center gap-3 flex-wrap">
          <Badge tone={stateTone(interview.processing_state)}>{interview.processing_state}</Badge>
          <span className="text-xs text-slate-300">{progress?.display || '—'}</span>
          {saveIndicator && <span className="text-[10px] text-slate-500">{saveIndicator}</span>}
        </div>
        {err && <div className="text-xs text-rose-400">{err}</div>}

        <div className="flex items-center gap-2 flex-wrap text-xs">
          <span className="text-slate-400">Mode:</span>
          <button
            disabled={busy || locked}
            onClick={() => onSwitchMode('GUIDED_QUESTIONS')}
            className={`px-2 py-1 rounded ${interview.mode === 'GUIDED_QUESTIONS' ? 'bg-sky-700 text-sky-50' : 'bg-slate-700'} disabled:opacity-40`}>
            Guided Questions
          </button>
          <button
            disabled={busy || locked}
            onClick={() => onSwitchMode('FREEFORM_NARRATIVE')}
            className={`px-2 py-1 rounded ${interview.mode === 'FREEFORM_NARRATIVE' ? 'bg-sky-700 text-sky-50' : 'bg-slate-700'} disabled:opacity-40`}>
            Freeform Narrative
          </button>
          <span className="ml-auto">
            <button
              disabled={busy || locked}
              onClick={onComplete}
              className="px-3 py-1 rounded bg-emerald-700 hover:bg-emerald-600 disabled:opacity-40"
            >
              {terminal ? 'Interview Complete' : 'Mark Interview Complete'}
            </button>
          </span>
        </div>
        <div className="text-[10px] text-slate-500">
          Completion triggers interview processing (actor extraction). It does <strong>not</strong> start legal analysis.
          Legal analysis remains behind the <em>Submit for Legal Analysis</em> control on the Dashboard.
        </div>
      </div>

      {interview.mode === 'GUIDED_QUESTIONS' ? (
        <GuidedQuestions
          interview={interview}
          locked={locked}
          onAnswerChange={onAnswerChange}
        />
      ) : (
        <FreeformNarrative
          interview={interview}
          locked={locked}
          onNarrativeChange={onNarrativeChange}
        />
      )}
    </div>
  )
}

function GuidedQuestions({ interview, locked, onAnswerChange }) {
  const questions = [...(interview.questions || [])].sort((a, b) => a.order_index - b.order_index)
  return (
    <section className="space-y-3">
      {questions.map((q) => (
        <div key={q.id} className="border border-slate-700 rounded p-3 bg-slate-800">
          <div className="flex justify-between items-start gap-2">
            <label className="text-sm text-slate-100">{q.prompt}</label>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${q.answered ? 'bg-emerald-700 text-emerald-50' : 'bg-slate-600 text-slate-300'}`}>
              {q.answered ? 'answered' : 'not yet'}
            </span>
          </div>
          <textarea
            disabled={locked}
            defaultValue={q.answer_text || ''}
            onBlur={(e) => onAnswerChange(q.id, e.target.value)}
            rows={q.completion_kind === 'LONG_TEXT' ? 4 : 2}
            className="w-full mt-2 text-sm p-2 rounded bg-slate-900 border border-slate-600 disabled:opacity-60"
            placeholder={q.completion_kind === 'LONG_TEXT' ? 'Type your answer… (min 20 chars)' : 'Type your answer…'}
          />
        </div>
      ))}
      {questions.length === 0 && (
        <div className="text-xs text-slate-500">No questions loaded.</div>
      )}
    </section>
  )
}

function FreeformNarrative({ interview, locked, onNarrativeChange }) {
  return (
    <section className="border border-slate-700 rounded p-3 bg-slate-800 space-y-2">
      <div className="text-sm text-slate-100">
        Paste or type a full interview narrative. On completion, the system extracts
        names and entities and populates the actor roster.
      </div>
      <textarea
        disabled={locked}
        defaultValue={interview.narrative_text || ''}
        onBlur={(e) => onNarrativeChange(e.target.value)}
        rows={18}
        className="w-full text-sm p-2 rounded bg-slate-900 border border-slate-600 disabled:opacity-60"
        placeholder="Paste or type the full interview narrative here…"
      />
      <div className="text-[10px] text-slate-500">
        Changes auto-save on blur. Click <em>Mark Interview Complete</em> to trigger actor extraction.
      </div>
    </section>
  )
}
