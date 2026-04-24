/**
 * CaseAuthority page — attorney review surface for provisional CACI decisions.
 *
 * Shows the case-to-authority map. Attorney can ACCEPT, REJECT, or REPLACE each
 * CACI for this case. Decisions are case-scoped.
 */
import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { caseAuthorityApi } from '../api/client'
import CaciAuthorityPanel from '../components/CaciAuthorityPanel'

export default function CaseAuthority() {
  const { id: caseId } = useParams()
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState(null)

  async function load() {
    setLoading(true)
    setErr(null)
    try {
      const data = await caseAuthorityApi.map(caseId)
      setRows(data)
    } catch (e) {
      setErr(e.message || 'load failed')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [caseId])

  if (loading) return <div className="p-6 text-slate-300">Loading authority map…</div>
  if (err) return <div className="p-6 text-rose-400">{err}</div>

  const pending = rows.filter((r) => r.authority?.requires_attorney_review)
  const decided = rows.filter((r) => !r.authority?.requires_attorney_review)

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Case Authority — Case #{caseId}</h1>
        <Link to={`/case/${caseId}`} className="text-sm text-sky-400 hover:underline">
          ← back to case
        </Link>
      </div>

      <div className="text-sm text-slate-400">
        Provisional CACI authority must be accepted, rejected, or replaced per case.
        Decisions do not propagate to other cases. Supersession, not overwrite.
      </div>

      <section>
        <h2 className="text-lg font-semibold mb-2">
          Pending review ({pending.length})
        </h2>
        {pending.length === 0 ? (
          <div className="text-sm text-slate-500">Nothing pending.</div>
        ) : (
          <div className="space-y-3">
            {pending.map((r) => (
              <CaciAuthorityPanel
                key={r.caci_id}
                caseId={parseInt(caseId, 10)}
                caciId={r.caci_id}
                authority={r.authority}
                onChange={load}
              />
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-2">Decided ({decided.length})</h2>
        {decided.length === 0 ? (
          <div className="text-sm text-slate-500">No decisions yet.</div>
        ) : (
          <div className="space-y-3">
            {decided.map((r) => (
              <CaciAuthorityPanel
                key={r.caci_id}
                caseId={parseInt(caseId, 10)}
                caciId={r.caci_id}
                authority={r.authority}
                onChange={load}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
