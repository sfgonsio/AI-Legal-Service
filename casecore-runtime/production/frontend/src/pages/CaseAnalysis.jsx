/**
 * CaseAnalysis — renders GET /cases/{id}/analysis.
 *
 * No backend logic changes. Pure display of the analysis blob produced by
 * brain.analysis_runner:
 *   - COAs (name, confidence, coverage, per-element status)
 *   - Burdens (element, BoP / BoPP, standard)
 *   - Remedies (grouped by COA, confidence, grounding)
 *   - Complaint (parties, jurisdiction, allegations, causes of action, prayer)
 *   - Evidence mapping (Evidence → Event → Actor → Element → COA)
 *
 * Guardrails:
 *   - Every value has a fallback — no literal "undefined" reaches the DOM.
 *   - When the case is pre-analysis (409), render a clear gate message
 *     instead of a blank page.
 *   - When the case is analyzed but has 0 COAs (edge case), every section
 *     still renders with a "nothing to show" explanation.
 */
import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { analysisApi, caseApi } from '../api/client'

// ---------------- utilities ----------------

function safe(v, fallback = '—') {
  if (v === null || v === undefined) return fallback
  if (typeof v === 'string' && v.trim() === '') return fallback
  return v
}

function pct(n, digits = 0) {
  if (typeof n !== 'number' || isNaN(n)) return '—'
  return `${(n * 100).toFixed(digits)}%`
}

function fmtDate(iso) {
  if (!iso) return '—'
  try { return new Date(iso).toLocaleString() } catch { return iso }
}

function Chip({ children, tone = 'slate' }) {
  const map = {
    slate: 'bg-slate-700 text-slate-100',
    sky: 'bg-sky-700 text-sky-50',
    amber: 'bg-amber-700 text-amber-50',
    emerald: 'bg-emerald-700 text-emerald-50',
    rose: 'bg-rose-700 text-rose-50',
    gray: 'bg-slate-600 text-slate-200',
  }
  return <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${map[tone]}`}>{children}</span>
}

function statusTone(s) {
  return { SUPPORTED: 'emerald', PARTIAL: 'amber', UNSUPPORTED: 'rose' }[s] || 'slate'
}

function categoryTone(c) {
  return {
    compensatory: 'emerald',
    restitution: 'sky',
    punitive: 'rose',
    injunctive: 'amber',
    declaratory: 'slate',
    costs_fees_interest: 'slate',
  }[c] || 'slate'
}

function Section({ title, count, defaultOpen = true, children, hint }) {
  return (
    <details className="border border-slate-700 rounded bg-slate-800" open={defaultOpen}>
      <summary className="cursor-pointer px-3 py-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-slate-100">{title}</span>
          {typeof count === 'number' && <Chip tone="slate">{count}</Chip>}
        </div>
        {hint && <span className="text-[10px] text-slate-500">{hint}</span>}
      </summary>
      <div className="px-3 pb-3 pt-0">{children}</div>
    </details>
  )
}

// ---------------- page ----------------

export default function CaseAnalysis() {
  const { id: caseId } = useParams()
  const [caseData, setCaseData] = useState(null)
  const [data, setData] = useState(null)
  const [err, setErr] = useState(null)
  const [gate, setGate] = useState(null)     // 409 details from server

  const load = useCallback(async () => {
    setErr(null); setGate(null)
    try {
      setCaseData(await caseApi.get(caseId))
    } catch {
      setCaseData(null)
    }
    try {
      const r = await analysisApi.get(caseId)
      setData(r)
    } catch (e) {
      const msg = e?.message || String(e)
      // Our fetch wrapper throws with status in the message; extract 409 payload if possible
      if (msg.includes('409')) {
        setGate({ message: msg })
      } else {
        setErr(msg)
      }
    }
  }, [caseId])

  useEffect(() => { load() }, [load])

  // ---------- states ----------

  if (err) {
    return (
      <div className="p-6 max-w-4xl mx-auto space-y-3">
        <PageHeader caseData={caseData} caseId={caseId} />
        <div className="text-rose-400 text-sm border border-rose-700 bg-rose-900/30 rounded p-3">
          Failed to load analysis: {err}
        </div>
      </div>
    )
  }

  if (gate) {
    return (
      <div className="p-6 max-w-4xl mx-auto space-y-3">
        <PageHeader caseData={caseData} caseId={caseId} />
        <div className="border border-amber-700 bg-amber-900/30 rounded p-3 text-amber-100 text-sm space-y-1">
          <div className="font-semibold">Analysis not yet available</div>
          <div>
            This case has not yet completed <em>Submit for Legal Analysis</em>. Once
            an analysis run finishes, the COAs, burdens, remedies, complaint draft
            and evidence map will appear here.
          </div>
          <div className="pt-2">
            <Link to={`/case/${caseId}`} className="text-sky-400 hover:underline">← Return to case dashboard</Link>
          </div>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="p-6 max-w-4xl mx-auto space-y-3">
        <PageHeader caseData={caseData} caseId={caseId} />
        <div className="text-slate-400 text-sm">Loading analysis…</div>
      </div>
    )
  }

  const result = data.result || {}
  const run = data.run || {}
  const stats = result.stats || {}
  const coas = result.coas || []
  const burdens = result.burdens || []
  const remedies = result.remedies || []
  const complaint = result.complaint || null
  const em = result.evidence_map || null

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-4">
      <PageHeader caseData={caseData} caseId={caseId} />

      <div className="border border-slate-700 rounded bg-slate-800 p-3 text-xs text-slate-300 flex flex-wrap gap-3">
        <span className="font-mono">run_id: {safe(run.run_id)}</span>
        <span>state: <Chip tone="emerald">{safe(run.state)}</Chip></span>
        <span>triggered: {fmtDate(run.triggered_at)}</span>
        <span>completed: {fmtDate(run.completed_at)}</span>
        <span>by: {safe(run.triggered_by_actor_id)}</span>
      </div>

      <div className="border border-slate-700 rounded bg-slate-800 p-3 text-xs text-slate-300 flex flex-wrap gap-3">
        <span>timeline events: <span className="font-mono text-slate-100">{safe(stats.timeline_events, 0)}</span></span>
        <span>actors: <span className="font-mono text-slate-100">{safe(stats.actors, 0)}</span></span>
        <span>documents: <span className="font-mono text-slate-100">{safe(stats.documents, 0)}</span></span>
        <span>interviews: <span className="font-mono text-slate-100">{safe(stats.interviews, 0)}</span></span>
        <span>COA candidates: <span className="font-mono text-slate-100">{safe(stats.coa_candidates, 0)}</span></span>
      </div>

      {result.provenance?.authority_grounding && (
        <div className="border border-emerald-700 bg-emerald-900/20 rounded p-3 text-[11px] text-emerald-100">
          <span className="font-semibold">Authority provenance:</span> {result.provenance.authority_grounding}
        </div>
      )}

      <Section title="Causes of Action" count={coas.length} hint={coas.length ? 'supported / partial / unsupported per element' : null}>
        <CoasPanel coas={coas} />
      </Section>

      <Section title="Burden Mapping" count={burdens.length} defaultOpen={false}>
        <BurdensPanel burdens={burdens} />
      </Section>

      <Section title="Remedies" count={remedies.length} defaultOpen={false}>
        <RemediesPanel remedies={remedies} />
      </Section>

      <Section title="Complaint Draft" defaultOpen={false}
        hint={complaint ? `${complaint.causes_of_action?.length || 0} COAs · ${complaint.general_allegations?.length || 0} allegations` : null}>
        <ComplaintPanel complaint={complaint} />
      </Section>

      <Section title="Evidence Mapping" count={em?.total_edges ?? 0} defaultOpen={false}
        hint={em ? `${em.total_edges} edges · ${em.coverage_per_coa?.length || 0} COAs covered` : null}>
        <EvidencePanel em={em} />
      </Section>
    </div>
  )
}

// ---------------- panels ----------------

function PageHeader({ caseData, caseId }) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-2xl font-semibold text-slate-100">Analysis — Case #{caseId}</h1>
        {caseData && (
          <div className="text-sm text-slate-400">
            {safe(caseData.name)} · {safe(caseData.plaintiff)} v. {safe(caseData.defendant)} · {safe(caseData.court)}
          </div>
        )}
      </div>
      <Link to={`/case/${caseId}`} className="text-sm text-sky-400 hover:underline">← back to case</Link>
    </div>
  )
}

function CoasPanel({ coas }) {
  if (!coas.length) {
    return <EmptyHint text="No causes of action produced by this run. Check the evidence mapping and timeline." />
  }
  return (
    <ul className="space-y-3">
      {coas.map((c) => (
        <li key={c.caci_id || c.name} className="border border-slate-700 rounded p-3 bg-slate-900/40">
          <header className="flex items-start justify-between gap-3">
            <div>
              <div className="text-slate-100 font-semibold">
                {safe(c.name)} <span className="ml-2 text-[10px] text-slate-500 font-mono">{safe(c.caci_id)}</span>
              </div>
              <div className="text-[11px] text-slate-500 font-mono">
                coverage {pct(c.coverage_pct)} · confidence {pct(c.confidence)}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">{safe(c.rationale)}</div>
            </div>
            <AuthorityBadge a={c.authority} />
          </header>

          <ul className="mt-2 space-y-1">
            {(c.elements || []).map((s) => (
              <li key={s.element_id} className="text-xs border border-slate-700 rounded px-2 py-1 bg-slate-900/60">
                <div className="flex items-start justify-between gap-2">
                  <span className="text-slate-200">{safe(s.label)} <span className="ml-1 text-[10px] font-mono text-slate-500">{safe(s.element_id)}</span></span>
                  <div className="flex gap-1 flex-wrap">
                    <Chip tone={statusTone(s.status)}>{safe(s.status)}</Chip>
                    <Chip tone="slate">conf {pct(s.confidence)}</Chip>
                  </div>
                </div>
                <div className="mt-1 text-[10px] text-slate-500 flex flex-wrap gap-3">
                  <span>events: {s.supporting_event_ids?.length ?? 0}</span>
                  <span>docs: {s.supporting_document_ids?.length ?? 0}</span>
                  <span>interviews: {s.supporting_interview_ids?.length ?? 0}</span>
                  <span>actors: {s.actor_ids?.length ?? 0}</span>
                  {s.proof_types?.length ? <span>proof: {s.proof_types.join(', ')}</span> : null}
                </div>
              </li>
            ))}
          </ul>
        </li>
      ))}
    </ul>
  )
}

function AuthorityBadge({ a }) {
  if (!a) return null
  return (
    <div className="flex flex-col items-end gap-1 text-right shrink-0">
      <Chip tone={a.body_status === 'IMPORTED' ? 'emerald' : 'rose'}>{safe(a.body_status)}</Chip>
      <div className="text-[10px] text-slate-500 font-mono max-w-[16rem] truncate" title={a.title}>
        {safe(a.reference)} · {safe(a.body_length, 0)} chars
      </div>
      {a.certified ? <Chip tone="slate">certified</Chip> : null}
    </div>
  )
}

function BurdensPanel({ burdens }) {
  if (!burdens.length) return <EmptyHint text="No burden rows — upstream COA list is empty." />
  return (
    <div className="space-y-3">
      {burdens.map((b) => (
        <div key={b.caci_id} className="border border-slate-700 rounded bg-slate-900/40">
          <div className="px-3 py-2 border-b border-slate-700 text-sm text-slate-100 flex items-center justify-between">
            <span>{safe(b.name)} <span className="ml-2 text-[10px] font-mono text-slate-500">{safe(b.caci_id)}</span></span>
            <Chip tone="slate">authority {safe(b.authority_reference)}</Chip>
          </div>
          <table className="w-full text-xs">
            <thead className="text-slate-400">
              <tr>
                <th className="text-left px-2 py-1 font-normal">Element</th>
                <th className="text-left px-2 py-1 font-normal">BoP</th>
                <th className="text-left px-2 py-1 font-normal">BoPP</th>
                <th className="text-left px-2 py-1 font-normal">Standard</th>
                <th className="text-left px-2 py-1 font-normal">Status</th>
              </tr>
            </thead>
            <tbody>
              {(b.element_burdens || []).map((eb) => (
                <tr key={eb.element_id} className="border-t border-slate-800">
                  <td className="px-2 py-1 text-slate-200">
                    <span>{safe(eb.label)}</span>
                    <span className="ml-1 text-[10px] font-mono text-slate-500">{safe(eb.element_id)}</span>
                  </td>
                  <td className="px-2 py-1 font-mono text-slate-300">{safe(eb.burden_of_production)}</td>
                  <td className="px-2 py-1 font-mono text-slate-300">{safe(eb.burden_of_persuasion)}</td>
                  <td className="px-2 py-1 text-slate-300">{safe(eb.standard)}</td>
                  <td className="px-2 py-1"><Chip tone={statusTone(eb.status)}>{safe(eb.status)}</Chip></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  )
}

function RemediesPanel({ remedies }) {
  if (!remedies.length) return <EmptyHint text="No remedies — upstream COA list is empty." />
  return (
    <div className="space-y-3">
      {remedies.map((bundle) => (
        <div key={bundle.caci_id} className="border border-slate-700 rounded bg-slate-900/40">
          <div className="px-3 py-2 border-b border-slate-700 text-sm text-slate-100 flex items-center justify-between">
            <span>{safe(bundle.name)} <span className="ml-2 text-[10px] font-mono text-slate-500">{safe(bundle.caci_id)}</span></span>
            <Chip tone="slate">authority {safe(bundle.authority_reference)}</Chip>
          </div>
          <ul className="divide-y divide-slate-800">
            {(bundle.remedies || []).map((r, i) => (
              <li key={i} className="px-3 py-2 text-xs flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="text-slate-100">{safe(r.label)}</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">{safe(r.grounding)}</div>
                  {r.supporting_event_ids?.length ? (
                    <div className="text-[10px] text-slate-500 mt-0.5 font-mono">
                      supported by {r.supporting_event_ids.length} event{r.supporting_event_ids.length === 1 ? '' : 's'}
                    </div>
                  ) : null}
                </div>
                <div className="flex flex-col items-end gap-1 shrink-0">
                  <Chip tone={categoryTone(r.category)}>{safe(r.category).replaceAll('_', ' ')}</Chip>
                  <Chip tone="slate">conf {pct(r.confidence)}</Chip>
                </div>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}

function ComplaintPanel({ complaint }) {
  if (!complaint) return <EmptyHint text="No complaint draft — analysis did not produce one." />
  const parties = complaint.parties || []
  const allegations = complaint.general_allegations || []
  const coas = complaint.causes_of_action || []
  const prayer = complaint.prayer_for_relief || []
  return (
    <div className="space-y-3 text-sm text-slate-200">
      <section>
        <div className="text-xs text-slate-500 uppercase tracking-wide">Caption</div>
        <div>{safe(complaint.caption)}</div>
        <div className="text-xs text-slate-400">{safe(complaint.court)}{complaint.filed_on ? ` · filed ${fmtDate(complaint.filed_on)}` : ''}</div>
      </section>

      <section>
        <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Parties</div>
        <ul className="space-y-1">
          {parties.length === 0 ? <li className="text-xs text-slate-500">No parties.</li> :
            parties.map((p, i) => (
              <li key={i} className="text-xs">
                <Chip tone="sky">{safe(p.role)}</Chip>
                <span className="ml-2">{safe(p.name)}</span>
                {p.notes ? <span className="ml-2 text-slate-500">({safe(p.notes)})</span> : null}
              </li>
            ))}
        </ul>
      </section>

      <section>
        <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Jurisdiction and Venue</div>
        <div className="text-xs text-slate-300">{safe(complaint.jurisdiction_and_venue)}</div>
      </section>

      <section>
        <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">General Allegations ({allegations.length})</div>
        {allegations.length === 0 ? <div className="text-xs text-slate-500">No allegations.</div> :
          <ol className="space-y-1">
            {allegations.map((a) => (
              <li key={a.para_no} className="text-xs">
                <span className="font-mono text-slate-500">¶{safe(a.para_no)}</span>
                {a.date_label ? <span className="ml-2 text-slate-400">{safe(a.date_label)}</span> : null}
                <span className="ml-2">{safe(a.text)}</span>
                {(a.source_document_id || a.source_interview_id) && (
                  <span className="ml-2 text-[10px] text-slate-500 font-mono">
                    {a.source_document_id ? `doc #${a.source_document_id}` : `interview #${a.source_interview_id}`}
                  </span>
                )}
              </li>
            ))}
          </ol>}
      </section>

      <section>
        <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Causes of Action ({coas.length})</div>
        {coas.length === 0 ? <div className="text-xs text-slate-500">No causes of action.</div> :
          <ul className="space-y-2">
            {coas.map((coa) => (
              <li key={coa.count} className="border border-slate-700 rounded p-2 bg-slate-900/40">
                <div className="text-sm text-slate-100 flex items-center justify-between gap-2">
                  <span>{safe(coa.title)}</span>
                  <div className="flex gap-1 shrink-0">
                    <Chip tone={coa.authority_body_status === 'IMPORTED' ? 'emerald' : 'rose'}>{safe(coa.authority_body_status)}</Chip>
                    <Chip tone="slate">conf {pct(coa.confidence)}</Chip>
                  </div>
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">Against: {safe(coa.against)} · Authority: {safe(coa.authority_reference)}</div>

                {coa.element_support?.length > 0 && (
                  <ul className="mt-1 grid grid-cols-1 md:grid-cols-2 gap-1">
                    {coa.element_support.map((s, i) => (
                      <li key={i} className="text-[11px] text-slate-300 flex items-center gap-2">
                        <Chip tone={statusTone(s.status)}>{safe(s.status)}</Chip>
                        <span className="font-mono text-slate-500">{safe(s.element_id)}</span>
                        <span>{safe(s.label)}</span>
                      </li>
                    ))}
                  </ul>
                )}

                {coa.allegations?.length ? (
                  <details className="mt-1">
                    <summary className="cursor-pointer text-[11px] text-slate-500">{coa.allegations.length} element allegations</summary>
                    <ol className="mt-1 space-y-0.5">
                      {coa.allegations.map((a) => (
                        <li key={a.para_no} className="text-[11px] text-slate-300">
                          <span className="font-mono text-slate-500">¶{safe(a.para_no)}</span>
                          {a.date_label ? <span className="ml-2 text-slate-500">{safe(a.date_label)}</span> : null}
                          <span className="ml-2">{safe(a.text)}</span>
                        </li>
                      ))}
                    </ol>
                  </details>
                ) : null}
              </li>
            ))}
          </ul>}
      </section>

      <section>
        <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Prayer for Relief ({prayer.length})</div>
        {prayer.length === 0 ? <div className="text-xs text-slate-500">No prayer.</div> :
          <ol className="list-decimal ml-5 space-y-0.5">
            {prayer.map((p, i) => <li key={i} className="text-xs text-slate-200">{safe(p)}</li>)}
          </ol>}
      </section>

      {complaint.provenance && (
        <section className="border-t border-slate-800 pt-2">
          <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Provenance</div>
          <div className="text-[11px] text-slate-400">{safe(complaint.provenance.notes)}</div>
          <div className="text-[10px] text-slate-500 mt-1 font-mono">
            timeline_event_count {safe(complaint.provenance.timeline_event_count, 0)} · coa_count {safe(complaint.provenance.coa_count, 0)} · authority_grounded {String(!!complaint.provenance.authority_grounded)}
          </div>
        </section>
      )}
    </div>
  )
}

function EvidencePanel({ em }) {
  if (!em) return <EmptyHint text="No evidence map in this analysis run." />
  const edges = em.edges || []
  const coverage = em.coverage_per_coa || []
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[11px] text-slate-400">
        <div className="border border-slate-700 rounded px-2 py-1 bg-slate-900/40">
          Total events <span className="block font-mono text-slate-100">{safe(em.total_events, 0)}</span>
        </div>
        <div className="border border-slate-700 rounded px-2 py-1 bg-slate-900/40">
          Edges <span className="block font-mono text-slate-100">{safe(em.total_edges, 0)}</span>
        </div>
        <div className="border border-slate-700 rounded px-2 py-1 bg-slate-900/40">
          Actors referenced <span className="block font-mono text-slate-100">{em.actors_referenced?.length ?? 0}</span>
        </div>
        <div className="border border-slate-700 rounded px-2 py-1 bg-slate-900/40">
          COAs covered <span className="block font-mono text-slate-100">{coverage.length}</span>
        </div>
      </div>

      {coverage.length > 0 && (
        <div>
          <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Coverage per COA</div>
          <table className="w-full text-xs border border-slate-700 rounded bg-slate-900/40">
            <thead className="text-slate-400">
              <tr>
                <th className="text-left px-2 py-1 font-normal">COA</th>
                <th className="text-left px-2 py-1 font-normal">Elements</th>
                <th className="text-left px-2 py-1 font-normal">With evidence</th>
                <th className="text-left px-2 py-1 font-normal">Coverage</th>
                <th className="text-left px-2 py-1 font-normal">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {coverage.map((row, i) => (
                <tr key={i} className="border-t border-slate-800">
                  <td className="px-2 py-1 text-slate-200">
                    {safe(row.name)} <span className="ml-1 text-[10px] font-mono text-slate-500">{safe(row.caci_id)}</span>
                  </td>
                  <td className="px-2 py-1 font-mono text-slate-300">{safe(row.elements_total, 0)}</td>
                  <td className="px-2 py-1 font-mono text-slate-300">{safe(row.elements_with_evidence, 0)}</td>
                  <td className="px-2 py-1 font-mono text-slate-300">{pct(row.coverage_pct)}</td>
                  <td className="px-2 py-1 font-mono text-slate-300">{pct(row.confidence)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div>
        <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Edges (Evidence → Event → COA)</div>
        {edges.length === 0 ? <EmptyHint text="No edges." /> :
          <ul className="space-y-1">
            {edges.map((edge, i) => (
              <li key={i} className="text-xs border border-slate-700 rounded px-2 py-1 bg-slate-900/40">
                <div className="flex items-start justify-between gap-2">
                  <span className="truncate">
                    <Chip tone={edge.evidence?.source_kind === 'DOCUMENT' ? 'sky' : 'amber'}>
                      {safe(edge.evidence?.source_kind)}
                    </Chip>
                    <span className="ml-2 font-mono">{safe(edge.evidence?.label)}</span>
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {edge.event_timestamp ? fmtDate(edge.event_timestamp) : 'undated'}
                  </span>
                </div>
                <div className="text-slate-300 mt-1 line-clamp-2">{safe(edge.event_summary)}</div>
                {edge.coa_links?.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {edge.coa_links.map((l, j) => (
                      <Chip key={j} tone="slate">{safe(l.caci_id)} / {safe(l.element_id)} ({safe(l.element_status)})</Chip>
                    ))}
                  </div>
                )}
                {edge.actor_ids?.length > 0 && (
                  <div className="mt-1 text-[10px] text-slate-500 font-mono">actor_ids: {edge.actor_ids.join(', ')}</div>
                )}
              </li>
            ))}
          </ul>}
      </div>
    </div>
  )
}

function EmptyHint({ text }) {
  return <div className="text-xs text-slate-500 border border-dashed border-slate-700 rounded p-2">{text}</div>
}
