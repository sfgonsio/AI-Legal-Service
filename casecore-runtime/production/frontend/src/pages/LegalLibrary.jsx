/**
 * LegalLibrary — browse certified CACI / EVID / BPC records with full body text.
 *
 * Non-negotiable rendering rules (fixes the "undefined" / "No content available" bug):
 *   - Every article response has a body_status field: IMPORTED | NOT_IMPORTED | REVOKED | BLOCKED.
 *   - When body_status is IMPORTED, body_text is guaranteed non-empty; render it.
 *   - Otherwise, render the server-provided status_message verbatim — never a bare "undefined"
 *     and never "No content available" without an explanation.
 */
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { legalLibraryApi } from '../api/client'

const CODE_LABELS = {
  CACI: 'CACI (Jury Instructions)',
  EVID: 'Evidence Code',
  BPC: 'Business & Professions (Cannabis)',
}

function Badge({ children, tone = 'slate' }) {
  const map = {
    slate: 'bg-slate-700 text-slate-100',
    emerald: 'bg-emerald-700 text-emerald-50',
    amber: 'bg-amber-700 text-amber-50',
    sky: 'bg-sky-700 text-sky-50',
    rose: 'bg-rose-700 text-rose-50',
  }
  return <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${map[tone]}`}>{children}</span>
}

function bodyStatusTone(s) {
  if (s === 'IMPORTED') return 'emerald'
  if (s === 'NOT_IMPORTED') return 'amber'
  if (s === 'REVOKED') return 'rose'
  if (s === 'BLOCKED') return 'rose'
  return 'slate'
}

export default function LegalLibrary() {
  const [stats, setStats] = useState(null)
  const [list, setList] = useState(null)
  const [err, setErr] = useState(null)
  const [code, setCode] = useState('CACI')
  const [q, setQ] = useState('')
  const [selectedId, setSelectedId] = useState(null)
  const [selected, setSelected] = useState(null)
  const [loadingArticle, setLoadingArticle] = useState(false)

  const loadList = useCallback(async () => {
    try {
      setErr(null)
      const data = await legalLibraryApi.list({ code, q: q.trim() || undefined, limit: 500 })
      setList(data)
    } catch (e) {
      setErr(e.message || 'failed to load library list')
    }
  }, [code, q])

  useEffect(() => {
    legalLibraryApi.stats().then(setStats).catch((e) => setErr(e.message || 'stats failed'))
  }, [])

  useEffect(() => { loadList() }, [loadList])

  async function loadArticle(recordId) {
    setSelectedId(recordId)
    setLoadingArticle(true)
    setSelected(null)
    try {
      const rec = await legalLibraryApi.get(recordId)
      setSelected(rec)
    } catch (e) {
      setSelected({
        record_id: recordId,
        title: recordId,
        body_text: null,
        body_status: 'NOT_IMPORTED',
        status_message: e.message || 'Failed to load record from server.',
      })
    } finally {
      setLoadingArticle(false)
    }
  }

  const visible = list?.records || []

  return (
    <div className="p-6 space-y-4 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Legal Library</h1>
        <Link to="/" className="text-sm text-sky-400 hover:underline">← back</Link>
      </div>

      {stats && (
        <div className="text-xs text-slate-400 font-mono flex flex-wrap gap-3">
          <span>Root: {stats.root}</span>
          <span>{stats.total_records} records</span>
          {Object.entries(stats.by_code).map(([k, n]) => (
            <span key={k}>{k}: {n}</span>
          ))}
        </div>
      )}
      {stats && stats.missing_codes_hint && (
        <div className="text-[10px] text-amber-300">{stats.missing_codes_hint}</div>
      )}

      {err && <div className="text-rose-400 text-sm">{err}</div>}

      <div className="flex gap-2 flex-wrap">
        {Object.keys(CODE_LABELS).map((k) => (
          <button key={k}
            onClick={() => { setCode(k); setSelectedId(null); setSelected(null) }}
            className={`px-3 py-1 text-xs rounded ${code === k ? 'bg-sky-700 text-sky-50' : 'bg-slate-700 text-slate-200'}`}>
            {CODE_LABELS[k]}
          </button>
        ))}
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="filter by id or title…"
          className="flex-1 min-w-[200px] px-2 py-1 text-xs rounded bg-slate-900 border border-slate-600"
        />
      </div>

      <div className="grid grid-cols-12 gap-4">
        <aside className="col-span-12 md:col-span-4 border border-slate-700 rounded bg-slate-800 p-2 max-h-[70vh] overflow-y-auto">
          {!list ? (
            <div className="text-slate-500 text-xs">Loading…</div>
          ) : visible.length === 0 ? (
            <div className="text-slate-500 text-xs">No matching records.</div>
          ) : (
            <ul className="space-y-1">
              {visible.map((r) => (
                <li key={r.record_id}>
                  <button
                    onClick={() => loadArticle(r.record_id)}
                    className={`w-full text-left text-xs px-2 py-1 rounded flex items-center justify-between gap-2
                      ${selectedId === r.record_id ? 'bg-slate-700' : 'hover:bg-slate-700/50'}`}>
                    <span className="truncate">
                      <span className="font-mono text-slate-300">{r.record_id}</span>
                      <span className="ml-2 text-slate-200">{r.title}</span>
                    </span>
                    <Badge tone={bodyStatusTone(r.body_status)}>{r.body_status}</Badge>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>

        <article className="col-span-12 md:col-span-8 border border-slate-700 rounded bg-slate-800 p-4 min-h-[400px]">
          {!selectedId ? (
            <div className="text-slate-500 text-sm">Select a record on the left.</div>
          ) : loadingArticle ? (
            <div className="text-slate-400 text-sm">Loading article…</div>
          ) : selected ? (
            <ArticleBody rec={selected} />
          ) : null}
        </article>
      </div>
    </div>
  )
}

function ArticleBody({ rec }) {
  const imported = rec.body_status === 'IMPORTED'
  return (
    <div className="space-y-3">
      <header className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-slate-100">{rec.title}</h2>
          <div className="text-xs text-slate-400 font-mono mt-1 flex gap-3 flex-wrap">
            <span>{rec.record_id}</span>
            <span>{rec.code}</span>
            {rec.certified && <span>certified</span>}
            {rec.provisional && <span>provisional</span>}
            {typeof rec.body_length === 'number' && <span>{rec.body_length} chars</span>}
          </div>
        </div>
        <Badge tone={bodyStatusTone(rec.body_status)}>{rec.body_status}</Badge>
      </header>

      {!imported && (
        <div className="rounded border border-amber-700 bg-amber-900/30 p-3 text-xs text-amber-100">
          <div className="font-semibold mb-1">{rec.body_status.replaceAll('_', ' ')}</div>
          <div>
            {rec.status_message ||
             "This record's body text is not available. It has not been imported into the Legal Library corpus."}
          </div>
        </div>
      )}

      {imported && rec.body_text && (
        <section>
          <h3 className="text-sm font-semibold text-slate-300 mb-1">Body</h3>
          <pre className="whitespace-pre-wrap text-sm text-slate-100 bg-slate-900 border border-slate-700 rounded p-3 leading-relaxed">
{rec.body_text}
          </pre>
        </section>
      )}

      {rec.directions_for_use && (
        <section>
          <h3 className="text-sm font-semibold text-slate-300 mb-1">Directions for Use</h3>
          <pre className="whitespace-pre-wrap text-sm text-slate-200 bg-slate-900 border border-slate-700 rounded p-3">
{rec.directions_for_use}
          </pre>
        </section>
      )}

      {rec.sources_and_authority && (
        <section>
          <h3 className="text-sm font-semibold text-slate-300 mb-1">Sources and Authority</h3>
          <pre className="whitespace-pre-wrap text-xs text-slate-300 bg-slate-900 border border-slate-700 rounded p-3">
{rec.sources_and_authority}
          </pre>
        </section>
      )}

      {rec.structure && (
        <section className="text-xs text-slate-400">
          <h3 className="text-sm font-semibold text-slate-300 mb-1">Structure</h3>
          <div className="font-mono">
            {Object.entries(rec.structure).map(([k, v]) => (
              <div key={k}>{k}: {String(v)}</div>
            ))}
          </div>
        </section>
      )}

      {rec.tags && rec.tags.length > 0 && (
        <div className="flex gap-1 flex-wrap">
          {rec.tags.map((t) => <Badge key={t} tone="slate">{t}</Badge>)}
        </div>
      )}

      {rec.source && (
        <div className="text-[10px] text-slate-500 font-mono">
          source: {rec.source.type || '?'} · {rec.source.jurisdiction || '?'}
          {rec.source.edition && ` · edition ${rec.source.edition}`}
          {rec.source.url && <> · <a className="text-sky-400 hover:underline" href={rec.source.url} target="_blank" rel="noreferrer">{rec.source.url}</a></>}
        </div>
      )}
    </div>
  )
}
