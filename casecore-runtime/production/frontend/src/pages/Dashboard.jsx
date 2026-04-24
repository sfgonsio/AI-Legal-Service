import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { caseApi, weaponApi, strategyApi, coaApi } from '../api/client'
import BreadcrumbNav from '../components/BreadcrumbNav'
import CaseStrengthMeter from '../components/CaseStrengthMeter'
import CaseProgressBar from '../components/CaseProgressBar'
import UploadPanel from '../components/UploadPanel'
import IngestStatusList from '../components/IngestStatusList'
import ActorsList from '../components/ActorsList'
import UploadedDocsList from '../components/UploadedDocsList'
import IntakeButton from '../components/IntakeButton'

const POST_ANALYSIS_STATES = new Set(['PROCESSING', 'REVIEW_REQUIRED', 'APPROVED'])

export default function Dashboard() {
  const { id: caseId } = useParams()
  const navigate = useNavigate()
  const [caseData, setCaseData] = useState(null)
  const [weapons, setWeapons] = useState([])
  const [strategies, setStrategies] = useState([])
  const [coas, setCoas] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadData()
  }, [caseId])

  async function loadData() {
    try {
      setLoading(true)

      if (caseId) {
        // Load specific case and its progress first; only fetch analytical
        // data if the case is in a post-analysis state. Pre-analysis reads
        // would 409 at the API per SR-11.
        const caseData = await caseApi.get(caseId)
        setCaseData(caseData)
        if (POST_ANALYSIS_STATES.has(caseData.save_state)) {
          const [weapons, strategies, coas] = await Promise.all([
            weaponApi.list(caseId),
            strategyApi.list(caseId),
            coaApi.list(caseId).catch(() => []),
          ])
          setWeapons(weapons || [])
          setStrategies(strategies || [])
          setCoas(coas || [])
        } else {
          // pre-analysis: weapons/strategies are seeded data and remain
          // readable, but COA authority is gated.
          const [weapons, strategies] = await Promise.all([
            weaponApi.list(caseId),
            strategyApi.list(caseId),
          ])
          setWeapons(weapons || [])
          setStrategies(strategies || [])
          setCoas([])
        }
      } else {
        const cases = await caseApi.list()
        if (cases.length > 0) {
          const firstCase = cases[0]
          navigate(`/case/${firstCase.id}`)
        }
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="p-6 text-center">
        <div className="text-slate-400">Loading...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 text-center">
        <div className="text-red-400">Error: {error}</div>
      </div>
    )
  }

  if (!caseData) {
    return (
      <div className="p-6 text-center">
        <div className="text-slate-400">No case found</div>
      </div>
    )
  }

  const avgWeaponScore = weapons.length > 0
    ? weapons.reduce((sum, w) => sum + (w.evidence_score || 0), 0) / weapons.length
    : 0

  const navStack = [
    { label: 'Cases', path: '/' },
    { label: caseData.name, path: `/case/${caseData.id}` }
  ]

  return (
    <div className="min-h-screen bg-slate-900 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-start justify-between gap-4 mb-2">
          <BreadcrumbNav navStack={navStack} />
          <div className="flex gap-2 items-start">
            <IntakeButton caseId={caseData.id} />
            <button
              onClick={() => navigate('/legal-library')}
              className="text-left border border-slate-700 rounded px-3 py-1 bg-slate-800 hover:border-sky-500"
              title="Open Legal Library"
            >
              <div className="text-xs font-semibold text-slate-100">Legal Library</div>
              <div className="text-[10px] text-slate-400 font-mono">CACI · EVID · BPC</div>
            </button>
          </div>
        </div>

        <h1 className="text-4xl font-bold text-slate-100 mb-2">{caseData.name}</h1>
        <p className="text-slate-400 mb-4">
          {caseData.plaintiff} v. {caseData.defendant} • {caseData.court}
        </p>

        <div className="mb-8">
          <CaseProgressBar caseId={caseData.id} onChange={loadData} />
        </div>

        {!POST_ANALYSIS_STATES.has(caseData.save_state) && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-8">
            <UploadPanel caseId={caseData.id} onComplete={loadData} />
            <div className="space-y-4">
              <IngestStatusList caseId={caseData.id} />
              <UploadedDocsList caseId={caseData.id} onChange={loadData} />
              <ActorsList caseId={caseData.id} />
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="card">
            <div className="text-2xl font-mono font-bold text-blue-400 mb-2">
              {weapons.length}
            </div>
            <div className="text-sm text-slate-400">Weapons Loaded</div>
          </div>

          <div className="card">
            <div className="text-2xl font-mono font-bold text-emerald-400 mb-2">
              {strategies.length}
            </div>
            <div className="text-sm text-slate-400">Strategies Active</div>
          </div>

          <div className="card">
            <div className="text-2xl font-mono font-bold text-amber-400 mb-2">
              {coas.length}
            </div>
            <div className="text-sm text-slate-400">Causes of Action</div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="card">
            <h2 className="text-xl font-bold mb-4 text-slate-200">Case Strength</h2>
            <CaseStrengthMeter strength={avgWeaponScore} />
          </div>

          <div className="card">
            <h2 className="text-xl font-bold mb-4 text-slate-200">Pipeline Status</h2>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">Evidence Gathered</span>
                <span className="font-mono text-blue-400">{Math.round(avgWeaponScore)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Ready for Deposition</span>
                <span className="font-mono text-emerald-400">
                  {weapons.filter(w => w.status === 'deployed').length}/{weapons.length}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-12">
          <h2 className="text-2xl font-bold mb-6 text-slate-200">Strategies</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {strategies.map(strategy => (
              <button
                key={strategy.id}
                onClick={() => navigate(`/strategy/${strategy.id}`)}
                className="card hover:border-blue-500 transition-colors text-left group"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-2xl">{strategy.emoji || '⚔'}</span>
                      <h3 className="font-bold text-slate-200 group-hover:text-blue-400 transition-colors">
                        {strategy.name}
                      </h3>
                    </div>
                    <p className="text-sm text-slate-400 mt-2">
                      Value: {strategy.value_score.toFixed(0)}
                    </p>
                  </div>
                  <span className="text-blue-400 group-hover:text-blue-300">→</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="mt-12">
          <h2 className="text-2xl font-bold mb-6 text-slate-200">Top Weapons</h2>
          <div className="space-y-3">
            {weapons.slice(0, 5).map(weapon => (
              <button
                key={weapon.id}
                onClick={() => navigate(`/weapon/${weapon.id}`)}
                className="surface rounded p-4 hover:border-blue-500 transition-colors text-left w-full flex justify-between items-center group"
              >
                <div>
                  <div className="font-medium text-slate-200 group-hover:text-blue-400 transition-colors">
                    {weapon.strategy}
                  </div>
                  <div className="text-xs text-slate-500 mt-1">
                    {weapon.coa_ref} • Evidence: {weapon.evidence_score.toFixed(0)}
                  </div>
                </div>
                <span className="text-blue-400 group-hover:text-blue-300">→</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
