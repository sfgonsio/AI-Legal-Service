/**
 * IngestStatusList
 *
 * Polls /documents/case/{id}/ingest-status while any doc is in flight.
 * Displays per-document phase with plain-English labels, OCR hint for
 * image-like files stuck at extract_skipped, and error detail on failures.
 */
import { useCallback, useEffect, useState } from 'react'
import { documentApi } from '../api/client'

const PHASE_LABEL = {
  uploaded: 'saved',
  hashed: 'hashed',
  extracting: 'extracting text',
  extracted: 'text extracted',
  normalized: 'normalized',
  indexed: 'indexed',
  actor_extraction_running: 'extracting actors',
  actors_extracted: 'actors extracted',
  ingest_complete: 'complete',
  extract_skipped: 'stored (not processed)',
  ingest_failed: 'failed',
}

function phaseTone(p) {
  if (p === 'ingest_complete') return 'bg-emerald-700 text-emerald-50'
  if (p === 'ingest_failed') return 'bg-rose-700 text-rose-50'
  if (p === 'extract_skipped') return 'bg-slate-600 text-slate-200'
  if (p === 'uploaded') return 'bg-slate-600 text-slate-200'
  return 'bg-amber-700 text-amber-50 animate-pulse'
}

const IMAGE_LIKE = new Set(['image'])  // file_type bucket
const BINARY_LIKE = new Set(['binary'])

export default function IngestStatusList({ caseId }) {
  const [data, setData] = useState(null)
  const [err, setErr] = useState(null)

  const load = useCallback(async () => {
    try {
      setData(await documentApi.ingestStatus(caseId))
      setErr(null)
    } catch (e) {
      setErr(e.message || 'load failed')
    }
  }, [caseId])

  useEffect(() => { load() }, [load])

  useEffect(() => {
    if (!data) return
    if (data.in_flight_count === 0) return
    const t = setInterval(load, 1500)
    return () => clearInterval(t)
  }, [data, load])

  if (err) return <div className="text-rose-400 text-xs">{err}</div>
  if (!data) return <div className="text-slate-500 text-xs">Loading ingest status…</div>

  if (data.documents.length === 0) {
    return (
      <div className="border border-slate-700 rounded-md p-3 bg-slate-800 text-xs text-slate-500">
        No documents yet. Upload evidence to see ingest progress.
      </div>
    )
  }

  function messageFor(d) {
    // Prefer the explicit extraction_status when present — it is the most
    // accurate signal of what actually happened.
    const es = d.extraction_status
    if (es === 'OCR_REQUIRED' || d.is_scanned_pdf) {
      return 'OCR required — this file appears to be scanned. Text extraction not available yet; stored for reference.'
    }
    if (es === 'OCR_NOT_AVAILABLE') {
      return 'OCR not yet supported for this file type — stored for reference.'
    }
    if (es === 'EXTRACTION_FAILED') {
      return `Extraction failed${d.error_detail ? `: ${d.error_detail}` : ''}. Remove and re-upload to retry.`
    }
    if (es === 'UNSUPPORTED_TYPE') {
      return 'Unsupported file type — stored but not processed.'
    }
    if (d.ingest_phase === 'extract_skipped') {
      if (IMAGE_LIKE.has(d.file_type)) {
        return 'OCR required — scanned or image content. Stored for reference.'
      }
      if (BINARY_LIKE.has(d.file_type)) {
        return 'Unsupported file type — stored but not processed.'
      }
      if (d.error_detail) return d.error_detail
      return 'Stored but not processed.'
    }
    if (d.ingest_phase === 'ingest_failed') {
      return d.error_detail || 'Ingest failed. Remove and re-upload to retry.'
    }
    if (es === 'TEXT_EXTRACTION_COMPLETE' && typeof d.extraction_confidence === 'number') {
      return `Text extracted (${d.extraction_method || 'engine'} · confidence ${(d.extraction_confidence * 100).toFixed(0)}%)`
    }
    return null
  }

  return (
    <div className="border border-slate-700 rounded-md p-3 bg-slate-800">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-semibold text-slate-100">Ingest Status</h3>
        <div className="text-xs text-slate-400">
          {data.success_count} complete · {data.failure_count} failed · {data.in_flight_count} in flight
        </div>
      </div>

      <ul className="space-y-1 max-h-64 overflow-y-auto">
        {data.documents.map((d) => {
          const msg = messageFor(d)
          return (
            <li key={d.id} className="text-xs border-b border-slate-700/60 py-1 last:border-b-0">
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono truncate" title={d.folder ? `${d.folder}/${d.filename}` : d.filename}>
                  {d.folder ? `${d.folder}/` : ''}{d.filename}
                  {d.actor_mention_count > 0 && (
                    <span className="ml-1 text-slate-500">· {d.actor_mention_count} mention{d.actor_mention_count === 1 ? '' : 's'}</span>
                  )}
                </span>
                <span className={`px-2 py-0.5 rounded font-mono text-[10px] ${phaseTone(d.ingest_phase)}`}
                  title={d.ingest_phase}>
                  {PHASE_LABEL[d.ingest_phase] || d.ingest_phase}
                </span>
              </div>
              {msg && (
                <div className={`mt-0.5 text-[10px] ${d.ingest_phase === 'ingest_failed' ? 'text-rose-400' : 'text-slate-400'}`}>
                  {msg}
                </div>
              )}
            </li>
          )
        })}
      </ul>
    </div>
  )
}
