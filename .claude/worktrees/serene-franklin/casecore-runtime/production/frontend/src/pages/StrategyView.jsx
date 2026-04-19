import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { strategyApi, weaponApi } from '../api/client'
import BreadcrumbNav from '../components/BreadcrumbNav'

export default function StrategyView() {
  const { key: strategyId } = useParams()
  const navigate = useNavigate()
  const [strategy, setStrategy] = useState(null)
  const [weapons, setWeapons] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStrategy()
  }, [strategyId])

  async function loadStrategy() {
    try {
      setLoading(true)
      const data = await strategyApi.get(strategyId)
      setStrategy(data)

      // Load weapons for this strategy
      if (data.case_id) {
        const allWeapons = await weaponApi.list(data.case_id)
        const strategyWeapons = allWeapons.filter(w => w.strategy === data.name)
        setWeapons(strategyWeapons)
      }
    } catch (err) {
      console.error('Failed to load strategy:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="p-6">Loading...</div>
  if (!strategy) return <div className="p-6">Strategy not found</div>

  const navStack = [
    { label: 'Cases', path: '/' },
    { label: strategy.name, path: `/strategy/${strategy.id}` }
  ]

  return (
    <div className="min-h-screen bg-slate-900 p-8">
      <div className="max-w-5xl mx-auto">
        <BreadcrumbNav navStack={navStack} />

        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-4xl">{strategy.emoji || '⚔'}</span>
            <h1 className="text-4xl font-bold text-slate-100">
              {strategy.name}
            </h1>
          </div>
          <p className="text-slate-400">
            Strategic approach for maximum impact
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-12">
          <div className="card">
            <div className="text-3xl font-mono font-bold text-blue-400 mb-2">
              {strategy.value_score.toFixed(0)}
            </div>
            <div className="text-sm text-slate-400">Value Score</div>
          </div>

          <div className="card">
            <div className="text-3xl font-mono font-bold text-emerald-400 mb-2">
              {strategy.depo_impact.toFixed(0)}
            </div>
            <div className="text-sm text-slate-400">Deposition Impact</div>
          </div>

          <div className="card">
            <div className="text-3xl font-mono font-bold text-amber-400 mb-2">
              {strategy.trial_impact.toFixed(0)}
            </div>
            <div className="text-sm text-slate-400">Trial Impact</div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Rationale */}
          <div className="card">
            <h2 className="text-xl font-bold mb-4 text-slate-200">Rationale</h2>
            <p className="text-slate-300 leading-relaxed">
              {strategy.rationale}
            </p>
          </div>

          {/* Phases */}
          <div className="card">
            <h2 className="text-xl font-bold mb-4 text-slate-200">Execution Phases</h2>
            <div className="space-y-2 text-sm">
              {strategy.phases_json && Object.entries(strategy.phases_json).map(([key, value]) => (
                <div key={key} className="flex items-center gap-2">
                  <span className="text-blue-400">→</span>
                  <span className="capitalize text-slate-300">{key.replace('phase', 'Phase ')} {value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Weapons List */}
        <div className="mt-12">
          <h2 className="text-2xl font-bold mb-6 text-slate-200">
            {weapons.length} Weapons in This Strategy
          </h2>

          <div className="space-y-3">
            {weapons.map(weapon => (
              <button
                key={weapon.id}
                onClick={() => navigate(`/weapon/${weapon.id}`)}
                className="surface rounded p-4 hover:border-blue-500 transition-colors text-left w-full group"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="font-medium text-slate-200 group-hover:text-blue-400 transition-colors">
                      {weapon.question}
                    </div>
                    <div className="text-xs text-slate-500 mt-2 flex gap-4">
                      <span>{weapon.caci}</span>
                      <span>Evidence: {weapon.evidence_score.toFixed(0)}</span>
                      {weapon.perjury_trap && <span className="text-red-400">⚠ Perjury Trap</span>}
                    </div>
                  </div>
                  <span className="text-blue-400 group-hover:text-blue-300">→</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
