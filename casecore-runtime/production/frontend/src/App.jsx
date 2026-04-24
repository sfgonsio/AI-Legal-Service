import { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import WeaponDetail from './pages/WeaponDetail'
import StrategyView from './pages/StrategyView'
import DepositionRoom from './pages/DepositionRoom'
import CaseAuthority from './pages/CaseAuthority'
import CaseIntake from './pages/CaseIntake'
import LegalLibrary from './pages/LegalLibrary'
import CaseTimeline from './pages/CaseTimeline'
import CaseAnalysis from './pages/CaseAnalysis'

// Global drag/drop guard.
// Without this, if the user drops a file ANYWHERE on the page that isn't an
// explicit drop target, the browser navigates to / opens each file (often in
// a fresh blank tab per file). preventDefault on window dragover + drop
// suppresses that entirely. The UploadPanel's own drop handler still runs
// because its own handlers stopPropagation before bubbling to window.
function useGlobalDragDropGuard() {
  useEffect(() => {
    const prevent = (e) => {
      // Only intervene when the payload is actually files. This leaves other
      // drag/drop uses (text drags, internal re-ordering, etc.) untouched.
      if (e.dataTransfer && Array.from(e.dataTransfer.types || []).includes('Files')) {
        e.preventDefault()
      }
    }
    window.addEventListener('dragover', prevent, false)
    window.addEventListener('drop', prevent, false)
    return () => {
      window.removeEventListener('dragover', prevent, false)
      window.removeEventListener('drop', prevent, false)
    }
  }, [])
}

export default function App() {
  useGlobalDragDropGuard()
  return (
    <Router>
      <div className="min-h-screen bg-slate-900 text-slate-100">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/case/:id" element={<Dashboard />} />
          <Route path="/case/:id/authority" element={<CaseAuthority />} />
          <Route path="/case/:id/intake" element={<CaseIntake />} />
          <Route path="/legal-library" element={<LegalLibrary />} />
          <Route path="/case/:id/timeline" element={<CaseTimeline />} />
          <Route path="/case/:id/analysis" element={<CaseAnalysis />} />
          <Route path="/weapon/:id" element={<WeaponDetail />} />
          <Route path="/strategy/:key" element={<StrategyView />} />
          <Route path="/deposition/:id" element={<DepositionRoom />} />
        </Routes>
      </div>
    </Router>
  )
}
