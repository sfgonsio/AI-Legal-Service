/**
 * UploadedDocsList
 *
 * Lists documents already stored for the case, grouped by folder, with a
 * Delete button per row. Uses the existing /documents endpoints.
 *
 * Complements UploadPanel (which shows in-flight upload rows) and
 * IngestStatusList (which shows ingest phase progress). No legal/analytical
 * fields rendered.
 */
import { useCallback, useEffect, useState } from 'react'
import { documentApi } from '../api/client'

function humanBytes(n) {
  if (!n && n !== 0) return '—'
  const u = ['B', 'KB', 'MB', 'GB']
  let i = 0; let x = n
  while (x >= 1024 && i < u.length - 1) { x /= 1024; i++ }
  return `${x.toFixed(x < 10 && i > 0 ? 1 : 0)} ${u[i]}`
}

export default function UploadedDocsList({ caseId, onChange }) {
  const [docs, setDocs] = useState(null)
  const [err, setErr] = useState(null)
  const [busyId, setBusyId] = useState(null)

  const load = useCallback(async () => {
    try {
      const rows = await documentApi.list(caseId)
      setDocs(rows)
      setErr(null)
    } catch (e) {
      setErr(e.message || 'load failed')
    }
  }, [caseId])

  useEffect(() => { load() }, [load])

  async function onDelete(docId) {
    if (!confirm('Delete this document? This removes it from the case and from storage if no other case references it.')) return
    setBusyId(docId)
    try {
      await documentApi.delete(docId)
      await load()
      if (onChange) await onChange()
    } catch (e) {
      setErr(e.message || 'delete failed')
    } finally {
      setBusyId(null)
    }
  }

  if (err) return <div className="text-rose-400 text-xs">{err}</div>
  if (!docs) return <div className="text-slate-500 text-xs">Loading documents…</div>

  if (docs.length === 0) {
    return (
      <div className="border border-slate-700 rounded-md p-3 bg-slate-800 text-xs text-slate-500">
        No documents yet.
      </div>
    )
  }

  // Group by folder (sorted)
  const grouped = {}
  for (const d of docs) {
    const key = d.folder || '(root)'
    if (!grouped[key]) grouped[key] = []
    grouped[key].push(d)
  }
  const folders = Object.keys(grouped).sort()

  return (
    <div className="border border-slate-700 rounded-md p-3 bg-slate-800 space-y-2">
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-semibold text-slate-100">Documents</h3>
        <span className="text-xs text-slate-400">{docs.length} total</span>
      </div>
      {folders.map((folder) => (
        <section key={folder}>
          <div className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">{folder}</div>
          <ul className="space-y-1">
            {grouped[folder].sort((a, b) => a.filename.localeCompare(b.filename)).map((d) => (
              <li key={d.id} className="text-xs flex items-center justify-between gap-2 border border-slate-700 rounded px-2 py-1">
                <span className="font-mono truncate" title={d.filename}>
                  {d.filename}
                  <span className="ml-2 text-slate-500">· {humanBytes(d.byte_size || 0)} · {d.file_type || '?'}</span>
                  {d.archive_relative_path && (
                    <span className="ml-2 text-amber-300">
                      (from archive #{d.archive_id}: {d.archive_relative_path})
                    </span>
                  )}
                </span>
                <button
                  disabled={busyId === d.id}
                  onClick={() => onDelete(d.id)}
                  className="px-2 py-0.5 text-[10px] rounded bg-rose-800 hover:bg-rose-700 disabled:opacity-40"
                >
                  {busyId === d.id ? 'deleting…' : 'Delete'}
                </button>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  )
}
