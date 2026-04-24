/**
 * CaseTimeline — simple vertical timeline.
 *
 * Shows TimelineEvent rows grouped by date. Includes a "Rebuild timeline"
 * action that calls POST /timeline/{case_id}/build. No legal-analysis
 * signals are rendered — this is a pre-analysis view.
 */
import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { timelineApi } from '../api/client'

function Chip({ children, tone = 'slate' }) {
  const map = {
    slate: 'bg-slate-700 text-slate-100',
    sky: 'bg-sky-700 text-sky-50',
    amber: 'bg-amber-700 text-amber-50',
    emerald: 'bg-emerald-700 text-emerald-50',
    rose: 'bg-rose-700 text-rose-50',
  }
  return <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${map[tone]}`}>{children}</span>
}

function eventTypeTone(t) {
  return {
    COMMUNICATION: 'sky',
    MEETING: 'slate',
    PAYMENT: 'emerald',
    FILING: 'amber',
    NOTICE: 'amber',
    AGREEMENT: 'sky',
    BREACH: 'rose',
    TRANSACTION: 'emerald',
    OTHER: 'slate',
  }[t] || 'slate'
}

function relationTone(r) {
  return {
    SUPPORTS: 'emerald',
    WEAKENS: 'amber',
    CONTRADICTS: 'rose',
    NEUTRAL: 'slate',
  }[r] || 'slate'
}

function elementTone(t) {
  return {
    COA_ELEMENT: 'sky',
    BURDEN_OF_PRODUCTION: 'amber',
    BURDEN_OF_PERSUASION: 'amber',
    REMEDY: 'emerald',
    EVIDENCE_ADMISSIBILITY: 'slate',
    PROCEDURAL: 'slate',
  }[t] || 'slate'
}

function LegalLayer({ ev }) {
  const flags = ev.strategy || {}
  const mappings = ev.legal_mappings || []
  const anyStrategy = flags.deposition_target || flags.interrogatory_target || flags.document_request_target
  if (!anyStrategy && mappings.length === 0 && ev.claim_relation === 'NEUTRAL') return null
  return (
    <div className="mt-2 pt-2 border-t border-slate-700 space-y-1">
      <div className="flex flex-wrap gap-1 items-center">
        <span className="text-[10px] text-slate-500 uppercase tracking-wide mr-1">Legal layer</span>
        <Chip tone={relationTone(ev.claim_relation)}>claim:{ev.claim_relation.toLowerCase()}</Chip>
        {flags.deposition_target && <Chip tone="sky">depo target</Chip>}
        {flags.interrogatory_target && <Chip tone="sky">rog target</Chip>}
        {flags.document_request_target && <Chip tone="sky">doc req target</Chip>}
      </div>
      {ev.strategy_rationale && (
        <div className="text-[10px] text-slate-500 font-mono">{ev.strategy_rationale}</div>
      )}
      {mappings.length > 0 && (
        <ul className="mt-1 space-y-0.5">
          {mappings.map((m, i) => (
            <li key={i} className="text-[11px] flex items-start gap-2">
              <Chip tone={elementTone(m.legal_element_type)}>{m.legal_element_type.toLowerCase().replaceAll('_', ' ')}</Chip>
              <span className="text-slate-300">
                {m.element_label}
                {m.element_reference && <span className="ml-1 text-slate-500 font-mono">({m.element_reference})</span>}
                <span className="ml-1 text-slate-500">· {(m.confidence * 100).toFixed(0)}%</span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function CaseTimeline() {
  const { id: caseId } = useParams()
  const [data, setData] = useState(null)
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  const [sourceFilter, setSourceFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')

  const load = useCallback(async () => {
    try {
      setErr(null)
      const d = await timelineApi.get(caseId, {
        source: sourceFilter || undefined,
        event_type: typeFilter || undefined,
      })
      setData(d)
    } catch (e) {
      setErr(e.message || 'failed to load timeline')
    }
  }, [caseId, sourceFilter, typeFilter])

  useEffect(() => { load() }, [load])

  async function onBuild() {
    setBusy(true); setErr(null)
    try {
      await timelineApi.build(caseId, true)
      await load()
    } catch (e) {
      setErr(e.message || 'build failed')
    } finally {
      setBusy(false)
    }
  }

  if (err && !data) return <div className="p-6 text-rose-400">{err}</div>
  if (!data) return <div className="p-6 text-slate-400">Loading timeline…</div>

  const totalSources = Object.entries(data.counts_by_source)
    .map(([k, v]) => `${k}: ${v}`).join(' · ')
  const totalTypes = Object.entries(data.counts_by_type)
    .map(([k, v]) => `${k}: ${v}`).join(' · ')

  return (
    <div className="p-6 space-y-4 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Timeline — Case #{caseId}</h1>
        <Link to={`/case/${caseId}`} className="text-sm text-sky-400 hover:underline">← back to case</Link>
      </div>

      <div className="border border-slate-700 rounded bg-slate-800 p-3 text-xs text-slate-300 space-y-2">
        <div className="flex flex-wrap items-center gap-3">
          <span className="font-mono">{data.total} events · known {data.known_count} · undated {data.unknown_count}</span>
          <button disabled={busy} onClick={onBuild}
            className="px-2 py-1 rounded bg-sky-700 hover:bg-sky-600 disabled:opacity-40">
            {busy ? 'Building…' : 'Rebuild Timeline'}
          </button>
          <select value={sourceFilter} onChange={(e) => setSourceFilter(e.target.value)}
            className="px-2 py-1 rounded bg-slate-900 border border-slate-600 text-xs">
            <option value="">all sources</option>
            <option value="INTERVIEW">interview</option>
            <option value="INGEST">ingest</option>
          </select>
          <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}
            className="px-2 py-1 rounded bg-slate-900 border border-slate-600 text-xs">
            <option value="">all types</option>
            {Object.keys(data.counts_by_type).sort().map((t) =>
              <option key={t} value={t}>{t.toLowerCase()}</option>
            )}
          </select>
        </div>
        <div className="text-slate-500">Sources: {totalSources || '—'}</div>
        <div className="text-slate-500">Types: {totalTypes || '—'}</div>
        {err && <div className="text-rose-400">{err}</div>}
      </div>

      {data.groups.length === 0 ? (
        <div className="border border-slate-700 rounded bg-slate-800 p-4 text-sm text-slate-400">
          No events yet. Upload evidence or complete an interview, then click
          <span className="mx-1 font-mono">Rebuild Timeline</span>
          to extract events.
        </div>
      ) : (
        <ol className="relative border-l border-slate-700 pl-4 space-y-6">
          {data.groups.map((g) => (
            <li key={g.key} className="relative">
              <div className="absolute -left-[11px] top-1 w-4 h-4 rounded-full bg-slate-600 border border-slate-800" />
              <div className="text-xs text-slate-400 font-mono mb-2">
                {g.label} <Chip tone="slate">{g.precision}</Chip>
              </div>
              <ul className="space-y-2">
                {g.events.map((ev) => (
                  <li key={ev.event_id}
                    className="border border-slate-700 rounded p-2 bg-slate-800">
                    <div className="flex items-start justify-between gap-2">
                      <div className="text-sm text-slate-100">{ev.summary}</div>
                      <div className="flex gap-1 flex-wrap items-start">
                        <Chip tone={eventTypeTone(ev.event_type)}>{ev.event_type.toLowerCase()}</Chip>
                        <Chip tone={ev.source === 'INTERVIEW' ? 'amber' : 'sky'}>{ev.source.toLowerCase()}</Chip>
                      </div>
                    </div>
                    <div className="mt-1 flex items-center gap-3 text-[10px] text-slate-500 font-mono">
                      {ev.raw_date_text && <span>{ev.raw_date_text}</span>}
                      <span>confidence {(ev.confidence * 100).toFixed(0)}%</span>
                      {ev.source_document_id && <span>doc #{ev.source_document_id}</span>}
                      {ev.source_interview_id && <span>interview #{ev.source_interview_id}</span>}
                    </div>
                    {ev.actors && ev.actors.length > 0 && (
                      <div className="mt-1 flex flex-wrap gap-1">
                        {ev.actors.map((a) => (
                          <Chip key={a.id} tone="emerald">{a.display_name}{a.role_hint ? ` (${a.role_hint})` : ''}</Chip>
                        ))}
                      </div>
                    )}
                    <LegalLayer ev={ev} />
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}
