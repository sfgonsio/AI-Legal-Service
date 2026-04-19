import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { weaponApi, documentApi } from '../api/client'
import BreadcrumbNav from '../components/BreadcrumbNav'
import AttorneyNotes from '../components/AttorneyNotes'
import ResponseTree from '../components/ResponseTree'
import SourceFileViewer from '../components/SourceFileViewer'

export default function WeaponDetail() {
  const { id: weaponId } = useParams()
  const navigate = useNavigate()
  const [weapon, setWeapon] = useState(null)
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(true)
  const [simulating, setSimulating] = useState(false)
  const [simulation, setSimulation] = useState(null)

  useEffect(() => {
    loadWeapon()
  }, [weaponId])

  async function loadWeapon() {
    try {
      setLoading(true)
      const data = await weaponApi.get(weaponId)
      setWeapon(data)

      // Load related documents
      if (data.docs_json?.docs) {
        const docPromises = data.docs_json.docs.map(docId =>
          documentApi.get(docId).catch(() => null)
        )
        const loadedDocs = await Promise.all(docPromises)
        setDocs(loadedDocs.filter(Boolean))
      }
    } catch (err) {
      console.error('Failed to load weapon:', err)
    } finally {
      setLoading(false)
    }
  }

  async function handleSimulate() {
    try {
      setSimulating(true)
      const result = await weaponApi.simulate(weaponId)
      setSimulation(result)
    } catch (err) {
      console.error('Simulation failed:', err)
    } finally {
      setSimulating(false)
    }
  }

  async function handleSaveNotes(notes) {
    try {
      await weaponApi.update(weaponId, { attorney_notes: notes })
      setWeapon({ ...weapon, attorney_notes: notes })
    } catch (err) {
      console.error('Failed to save notes:', err)
    }
  }

  if (loading) return <div className="p-6">Loading...</div>
  if (!weapon) return <div className="p-6">Weapon not found</div>

  const navStack = [
    { label: 'Cases', path: '/' },
    { label: weapon.coa_ref, path: '/' },
    { label: weapon.strategy, path: `/weapon/${weapon.id}` }
  ]

  return (
    <div className="min-h-screen bg-slate-900 p-8">
      <div className="max-w-4xl mx-auto">
        <BreadcrumbNav navStack={navStack} />

        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-100 mb-2">
            {weapon.strategy}
          </h1>
          <p className="text-slate-400">
            {weapon.coa_ref} • Evidence Score: {weapon.evidence_score.toFixed(0)}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Question */}
            <div className="card">
              <h2 className="text-lg font-bold mb-3 text-slate-200">The Question</h2>
              <p className="text-slate-300 text-lg italic">
                "{weapon.question}"
              </p>
            </div>

            {/* Strategy */}
            <div className="card">
              <h2 className="text-lg font-bold mb-3 text-slate-200">Strategy</h2>
              <div className="space-y-3 text-sm">
                <div>
                  <div className="text-slate-400 font-medium mb-1">Strengthens Jeremy:</div>
                  <div className="text-slate-300">{weapon.strengthens_jeremy}</div>
                </div>
                <div>
                  <div className="text-slate-400 font-medium mb-1">Weakens David:</div>
                  <div className="text-slate-300">{weapon.weakens_david}</div>
                </div>
              </div>
            </div>

            {/* Simulation */}
            <div className="card">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-bold text-slate-200">Opposition Response</h2>
                <button
                  onClick={handleSimulate}
                  disabled={simulating}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 text-white text-sm rounded transition-colors"
                >
                  {simulating ? 'Simulating...' : 'Simulate'}
                </button>
              </div>

              {simulation && (
                <ResponseTree responses={[simulation]} />
              )}
            </div>

            {/* Source Documents */}
            <div>
              <h2 className="text-lg font-bold mb-4 text-slate-200">Source Documents</h2>
              <div className="space-y-4">
                {docs.length > 0 ? (
                  docs.map(doc => (
                    <SourceFileViewer key={doc.id} document={doc} />
                  ))
                ) : (
                  <div className="text-slate-500 italic">No source documents attached</div>
                )}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Stats */}
            <div className="card">
              <h3 className="font-bold mb-4 text-slate-200">Quick Stats</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">Category</span>
                  <span className="font-mono">{weapon.category}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Status</span>
                  <span className="font-mono capitalize">{weapon.status}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Perjury Trap</span>
                  <span className="font-mono">{weapon.perjury_trap ? '⚠' : '—'}</span>
                </div>
              </div>
            </div>

            {/* Attorney Notes */}
            <AttorneyNotes
              initialValue={weapon.attorney_notes || ''}
              onSave={handleSaveNotes}
            />

            {/* Actions */}
            <div className="card">
              <button
                onClick={() => weaponApi.deploy(weaponId)}
                className="w-full py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded font-medium text-sm transition-colors"
              >
                Deploy This Weapon
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
