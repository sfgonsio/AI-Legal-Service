import { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { depositionApi } from '../api/client'
import { useWebSocket } from '../hooks/useWebSocket'
import BreadcrumbNav from '../components/BreadcrumbNav'

export default function DepositionRoom() {
  const { id: sessionId } = useParams()
  const [session, setSession] = useState(null)
  const [transcript, setTranscript] = useState('')
  const [testimony, setTestimony] = useState('')
  const [suggestions, setSuggestions] = useState(null)
  const [messages, setMessages] = useState([])
  const transcriptRef = useRef(null)

  const { isConnected, send } = useWebSocket(sessionId, (message) => {
    if (message.type === 'suggestion') {
      setSuggestions(message)
    }
  })

  useEffect(() => {
    loadSession()
  }, [sessionId])

  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight
    }
  }, [transcript])

  async function loadSession() {
    try {
      const data = await depositionApi.get(sessionId)
      setSession(data)
      setTranscript(data.transcript_text || '')
    } catch (err) {
      console.error('Failed to load session:', err)
    }
  }

  function handleAddTestimony() {
    if (!testimony.trim()) return

    const newTranscript = transcript
      ? `${transcript}\n\nWITNESS: ${testimony}`
      : `WITNESS: ${testimony}`

    setTranscript(newTranscript)
    setMessages([...messages, { type: 'testimony', text: testimony, timestamp: new Date() }])

    // Send to WebSocket for analysis
    send({
      type: 'testimony',
      text: testimony,
      witness_name: session?.witness_name || 'Unknown'
    })

    setTestimony('')
  }

  function handleSaveTranscript() {
    depositionApi.updateTranscript(sessionId, transcript)
  }

  function handleCloseSession() {
    depositionApi.close(sessionId)
  }

  if (!session) return <div className="p-6">Loading...</div>

  const navStack = [
    { label: 'Cases', path: '/' },
    { label: 'Depositions', path: '/' },
    { label: session.witness_name || 'Session', path: `/deposition/${session.id}` }
  ]

  return (
    <div className="min-h-screen bg-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        <BreadcrumbNav navStack={navStack} />

        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold text-slate-100 mb-2">
              Deposition: {session.witness_name || 'Unknown Witness'}
            </h1>
            <p className="text-slate-400">
              Session Status: <span className="font-mono capitalize">{session.status}</span>
            </p>
          </div>
          <div className="flex gap-2">
            <div className={`px-3 py-1 rounded text-sm font-medium ${
              isConnected ? 'bg-emerald-900 text-emerald-300' : 'bg-slate-700 text-slate-400'
            }`}>
              {isConnected ? '● Connected' : '○ Offline'}
            </div>
            <button
              onClick={handleCloseSession}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded transition-colors text-sm"
            >
              Close Session
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Transcript Panel */}
          <div className="lg:col-span-2">
            <div className="card flex flex-col h-[600px]">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-bold text-slate-200">Transcript</h2>
                <button
                  onClick={handleSaveTranscript}
                  className="text-xs px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded transition-colors"
                >
                  Save
                </button>
              </div>

              <div
                ref={transcriptRef}
                className="flex-1 bg-slate-900 rounded p-4 overflow-y-auto mb-4 font-mono text-sm text-slate-300 border border-slate-700"
              >
                {transcript || <span className="text-slate-600 italic">Transcript empty</span>}
              </div>

              <div className="space-y-3">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={testimony}
                    onChange={(e) => setTestimony(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleAddTestimony()}
                    placeholder="Enter witness testimony..."
                    className="flex-1 px-3 py-2 bg-slate-800 border border-slate-600 rounded text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                  <button
                    onClick={handleAddTestimony}
                    disabled={!testimony.trim() || !isConnected}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 text-white text-sm rounded transition-colors"
                  >
                    Add
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Suggestions Panel */}
          <div className="card h-[600px] overflow-y-auto">
            <h2 className="text-lg font-bold mb-4 text-slate-200 sticky top-0 bg-slate-800 -m-6 p-6 pb-4">
              AI Assistant
            </h2>

            {suggestions ? (
              <div className="space-y-4 text-sm">
                {/* Follow-up Questions */}
                {suggestions.follow_up_questions && (
                  <div>
                    <div className="font-bold text-slate-300 mb-2">Next Questions:</div>
                    <div className="space-y-2">
                      {suggestions.follow_up_questions.map((q, idx) => (
                        <div
                          key={idx}
                          className="bg-slate-800/50 rounded p-3 border-l-2 border-blue-500"
                        >
                          <div className="text-slate-200 italic">"{q.question}"</div>
                          <div className="text-xs text-slate-500 mt-2">
                            {q.strategy} • Score: {q.score}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Contradictions */}
                {suggestions.contradictions && suggestions.contradictions.length > 0 && (
                  <div>
                    <div className="font-bold text-red-400 mb-2">Contradictions Found:</div>
                    <div className="space-y-2">
                      {suggestions.contradictions.map((c, idx) => (
                        <div key={idx} className="bg-red-900/20 rounded p-3 border-l-2 border-red-500 text-red-300 text-xs">
                          {c.type === 'omission'
                            ? `Missing reference to: "${c.phrase}"`
                            : c.detail}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Perjury Flag */}
                {suggestions.perjury_flag && (
                  <div className="bg-amber-900/20 rounded p-3 border-l-2 border-amber-500">
                    <div className="font-bold text-amber-400 mb-1">Perjury Opportunity:</div>
                    <div className="text-xs text-amber-300">
                      {suggestions.perjury_flag.description}
                    </div>
                  </div>
                )}

                {!suggestions.follow_up_questions && !suggestions.contradictions && !suggestions.perjury_flag && (
                  <div className="text-slate-500 italic">Add testimony to see suggestions...</div>
                )}
              </div>
            ) : (
              <div className="text-slate-500 italic h-full flex items-center justify-center">
                {isConnected ? 'Waiting for testimony...' : 'Connecting to AI assistant...'}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
