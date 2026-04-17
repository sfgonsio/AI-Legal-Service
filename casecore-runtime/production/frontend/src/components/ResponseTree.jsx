import { useState } from 'react'

export default function ResponseTree({ responses = [] }) {
  const [expanded, setExpanded] = useState(0)

  if (!responses || responses.length === 0) {
    return (
      <div className="text-sm text-slate-500 italic">
        Run simulation to generate responses
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {responses.map((response, idx) => (
        <div key={idx} className="surface-subtle rounded p-4 border-l-2 border-blue-500">
          <button
            onClick={() => setExpanded(expanded === idx ? -1 : idx)}
            className="w-full text-left hover:text-blue-400 transition-colors font-medium text-sm flex items-center justify-between"
          >
            <span>Response Scenario {idx + 1}</span>
            <span>{expanded === idx ? '−' : '+'}</span>
          </button>

          {expanded === idx && (
            <div className="mt-4 space-y-3 text-sm">
              <div>
                <div className="text-slate-400 font-medium mb-1">David Says:</div>
                <div className="text-slate-300 italic">"{response.david_says || '...'}"</div>
              </div>

              <div>
                <div className="text-slate-400 font-medium mb-1">Your Counter:</div>
                <div className="text-slate-200">{response.counter || '...'}</div>
              </div>

              <div>
                <div className="text-slate-400 font-medium mb-1">Delta (Effect):</div>
                <div className="text-emerald-400">{response.delta || '...'}</div>
              </div>

              {response.perjury_evidence && (
                <div>
                  <div className="text-slate-400 font-medium mb-1">Perjury Flag:</div>
                  <div className="text-red-400">{response.perjury_evidence}</div>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
