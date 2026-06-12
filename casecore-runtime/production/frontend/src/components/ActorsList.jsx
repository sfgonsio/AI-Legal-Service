/**
 * ActorsList — full CRUD view of the case actor roster.
 *
 * Features:
 *   - grouped view (RESOLVED / CANDIDATE / AMBIGUOUS / ORGANIZATIONS)
 *   - source + provenance visible (INGEST / INTERVIEW / SEED / MANUAL)
 *   - create actor (inline form)
 *   - promote CANDIDATE/AMBIGUOUS -> RESOLVED
 *   - edit display name, role_hint, notes, entity_type, resolution_state
 *   - delete actor
 *   - merge: select 2+ rows, pick target, consolidate mentions
 *
 * Never reads analytical data.
 */
import { useCallback, useEffect, useState } from 'react'
import { actorApi } from '../api/client'

function Chip({ children, tone = 'slate' }) {
  const map = {
    slate: 'bg-slate-700 text-slate-100',
    emerald: 'bg-emerald-700 text-emerald-50',
    sky: 'bg-sky-700 text-sky-50',
    amber: 'bg-amber-700 text-amber-50',
    rose: 'bg-rose-700 text-rose-50',
  }
  return <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${map[tone]}`}>{children}</span>
}

function SourceChip({ source, interviewId }) {
  const label = interviewId ? `${source}:iv${interviewId}` : source
  const tone = source === 'MANUAL' ? 'sky' : source === 'SEED' ? 'emerald' : source === 'INTERVIEW' ? 'amber' : 'slate'
  return <Chip tone={tone}>{label}</Chip>
}

function ActorRow({ actor, selected, onToggleSelect, onSave, onDelete, onPromote }) {
  const [edit, setEdit] = useState(false)
  const [busy, setBusy] = useState(false)
  const [fields, setFields] = useState({
    display_name: actor.display_name,
    role_hint: actor.role_hint || '',
    entity_type: actor.entity_type,
    resolution_state: actor.resolution_state,
    notes: actor.notes || '',
  })

  async function save() {
    setBusy(true)
    try { await onSave(actor.id, fields); setEdit(false) }
    finally { setBusy(false) }
  }

  return (
    <li className="border border-slate-700 rounded px-2 py-1 text-xs">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <input type="checkbox" checked={selected} onChange={() => onToggleSelect(actor.id)} />
          <span className="font-mono truncate" title={actor.canonical_name}>{actor.display_name}</span>
          {actor.role_hint && <span className="text-slate-500">({actor.role_hint})</span>}
          <span className="text-slate-500">· {actor.mention_count} mention{actor.mention_count === 1 ? '' : 's'}</span>
        </div>
        <div className="flex items-center gap-2">
          <Chip tone={
            actor.entity_type === 'ORGANIZATION' ? 'sky' :
            actor.resolution_state === 'RESOLVED' ? 'emerald' :
            actor.resolution_state === 'AMBIGUOUS' ? 'amber' : 'slate'
          }>
            {actor.entity_type === 'ORGANIZATION' ? 'ORG' : actor.resolution_state}
          </Chip>
          <SourceChip source={actor.source} interviewId={actor.source_interview_id} />
          {(actor.resolution_state !== 'RESOLVED' && actor.entity_type !== 'ORGANIZATION') && (
            <button onClick={() => onPromote(actor)} disabled={busy}
              className="px-2 py-0.5 rounded bg-emerald-700 hover:bg-emerald-600">
              Resolve
            </button>
          )}
          <button onClick={() => setEdit((v) => !v)}
            className="px-2 py-0.5 rounded bg-slate-700 hover:bg-slate-600">
            {edit ? 'Cancel' : 'Edit'}
          </button>
          <button onClick={() => onDelete(actor)} disabled={busy}
            className="px-2 py-0.5 rounded bg-rose-800 hover:bg-rose-700">
            Delete
          </button>
        </div>
      </div>
      {edit && (
        <div className="mt-2 grid grid-cols-2 gap-2">
          <label className="text-slate-400 col-span-2">Display name
            <input className="w-full mt-0.5 px-2 py-1 rounded bg-slate-900 border border-slate-600"
              value={fields.display_name}
              onChange={(e) => setFields({ ...fields, display_name: e.target.value })} />
          </label>
          <label className="text-slate-400">Role hint
            <input className="w-full mt-0.5 px-2 py-1 rounded bg-slate-900 border border-slate-600"
              value={fields.role_hint}
              onChange={(e) => setFields({ ...fields, role_hint: e.target.value })} />
          </label>
          <label className="text-slate-400">Entity type
            <select className="w-full mt-0.5 px-2 py-1 rounded bg-slate-900 border border-slate-600"
              value={fields.entity_type}
              onChange={(e) => setFields({ ...fields, entity_type: e.target.value })}>
              <option>PERSON</option>
              <option>ORGANIZATION</option>
              <option>UNKNOWN</option>
            </select>
          </label>
          <label className="text-slate-400">Resolution state
            <select className="w-full mt-0.5 px-2 py-1 rounded bg-slate-900 border border-slate-600"
              value={fields.resolution_state}
              onChange={(e) => setFields({ ...fields, resolution_state: e.target.value })}>
              <option>RESOLVED</option>
              <option>CANDIDATE</option>
              <option>AMBIGUOUS</option>
            </select>
          </label>
          <label className="text-slate-400 col-span-2">Notes
            <textarea rows={2} className="w-full mt-0.5 px-2 py-1 rounded bg-slate-900 border border-slate-600"
              value={fields.notes}
              onChange={(e) => setFields({ ...fields, notes: e.target.value })} />
          </label>
          <div className="col-span-2">
            <button onClick={save} disabled={busy}
              className="px-2 py-1 rounded bg-sky-700 hover:bg-sky-600">Save</button>
          </div>
        </div>
      )}
    </li>
  )
}

function CreateActorForm({ caseId, onCreated }) {
  const [open, setOpen] = useState(false)
  const [fields, setFields] = useState({
    display_name: '', role_hint: '',
    entity_type: 'PERSON', resolution_state: 'RESOLVED', notes: '',
  })
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)

  async function submit() {
    if (!fields.display_name.trim()) { setErr('display_name is required'); return }
    setBusy(true); setErr(null)
    try {
      await actorApi.create({ case_id: caseId, ...fields })
      setFields({ display_name: '', role_hint: '', entity_type: 'PERSON', resolution_state: 'RESOLVED', notes: '' })
      setOpen(false)
      if (onCreated) await onCreated()
    } catch (e) {
      setErr(e.message || 'create failed')
    } finally { setBusy(false) }
  }

  if (!open) {
    return <button onClick={() => setOpen(true)}
      className="px-2 py-0.5 text-xs rounded bg-sky-700 hover:bg-sky-600">+ New Actor</button>
  }
  return (
    <div className="border border-slate-700 rounded p-2 space-y-2 bg-slate-900">
      <div className="grid grid-cols-2 gap-2 text-xs">
        <label className="text-slate-400 col-span-2">Display name
          <input className="w-full mt-0.5 px-2 py-1 rounded bg-slate-950 border border-slate-600"
            value={fields.display_name}
            onChange={(e) => setFields({ ...fields, display_name: e.target.value })} />
        </label>
        <label className="text-slate-400">Role hint
          <input className="w-full mt-0.5 px-2 py-1 rounded bg-slate-950 border border-slate-600"
            value={fields.role_hint}
            onChange={(e) => setFields({ ...fields, role_hint: e.target.value })} />
        </label>
        <label className="text-slate-400">Entity type
          <select className="w-full mt-0.5 px-2 py-1 rounded bg-slate-950 border border-slate-600"
            value={fields.entity_type}
            onChange={(e) => setFields({ ...fields, entity_type: e.target.value })}>
            <option>PERSON</option><option>ORGANIZATION</option><option>UNKNOWN</option>
          </select>
        </label>
        <label className="text-slate-400 col-span-2">Notes
          <input className="w-full mt-0.5 px-2 py-1 rounded bg-slate-950 border border-slate-600"
            value={fields.notes}
            onChange={(e) => setFields({ ...fields, notes: e.target.value })} />
        </label>
      </div>
      {err && <div className="text-[10px] text-rose-400">{err}</div>}
      <div className="flex gap-2">
        <button onClick={submit} disabled={busy} className="px-2 py-0.5 text-xs rounded bg-emerald-700 hover:bg-emerald-600">Create</button>
        <button onClick={() => { setOpen(false); setErr(null) }} className="px-2 py-0.5 text-xs rounded bg-slate-700">Cancel</button>
      </div>
    </div>
  )
}

export default function ActorsList({ caseId }) {
  const [data, setData] = useState(null)
  const [err, setErr] = useState(null)
  const [selected, setSelected] = useState(new Set())

  const load = useCallback(async () => {
    try {
      setData(await actorApi.list(caseId))
      setErr(null)
    } catch (e) { setErr(e.message || 'load failed') }
  }, [caseId])

  useEffect(() => { load() }, [load])

  const toggleSelect = (id) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id); else next.add(id)
      return next
    })
  }

  async function onSave(id, fields) {
    await actorApi.update(id, fields)
    await load()
  }

  async function onDelete(actor) {
    if (!confirm(`Delete actor "${actor.display_name}"? Mentions will also be removed.`)) return
    await actorApi.delete(actor.id)
    setSelected((prev) => { const n = new Set(prev); n.delete(actor.id); return n })
    await load()
  }

  async function onPromote(actor) {
    await actorApi.update(actor.id, { resolution_state: 'RESOLVED' })
    await load()
  }

  async function onMerge() {
    const ids = Array.from(selected)
    if (ids.length < 2) { alert('Select at least 2 actors to merge.'); return }
    const targetIdStr = prompt(`Target actor id? Choose one of: ${ids.join(', ')}`)
    const targetId = parseInt(targetIdStr, 10)
    if (!ids.includes(targetId)) { alert('Invalid target.'); return }
    const sources = ids.filter((i) => i !== targetId)
    await actorApi.merge(sources, targetId)
    setSelected(new Set())
    await load()
  }

  if (err) return <div className="text-rose-400 text-xs">{err}</div>
  if (!data) return <div className="text-slate-500 text-xs">Loading actors…</div>
  const c = data.counts

  return (
    <div className="border border-slate-700 rounded-md p-3 bg-slate-800 space-y-3">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <h3 className="text-sm font-semibold text-slate-100">Actors</h3>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-mono">
            {c.total} · {c.resolved} resolved · {c.candidate} candidate · {c.ambiguous} ambiguous · {c.organizations} orgs
          </span>
          <CreateActorForm caseId={caseId} onCreated={load} />
          {selected.size >= 2 && (
            <button onClick={onMerge}
              className="px-2 py-0.5 text-xs rounded bg-amber-700 hover:bg-amber-600">
              Merge {selected.size} →
            </button>
          )}
        </div>
      </div>

      {['resolved', 'candidate', 'ambiguous', 'organizations'].map((k) => {
        const rows = data[k] || []
        if (rows.length === 0) return null
        return (
          <section key={k}>
            <div className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">{k}</div>
            <ul className="space-y-1">
              {rows.map((a) => (
                <ActorRow
                  key={a.id}
                  actor={a}
                  selected={selected.has(a.id)}
                  onToggleSelect={toggleSelect}
                  onSave={onSave}
                  onDelete={onDelete}
                  onPromote={onPromote}
                />
              ))}
            </ul>
          </section>
        )
      })}

      {c.total === 0 && (
        <div className="text-xs text-slate-500">
          No actors yet. Complete the intake interview or upload evidence — the roster populates automatically.
        </div>
      )}
    </div>
  )
}
