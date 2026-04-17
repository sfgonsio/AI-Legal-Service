import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import WeaponDetail from './pages/WeaponDetail'
import StrategyView from './pages/StrategyView'
import DepositionRoom from './pages/DepositionRoom'

export default function App() {
  return (
    <Router>
      <div className="min-h-screen bg-slate-900 text-slate-100">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/case/:id" element={<Dashboard />} />
          <Route path="/weapon/:id" element={<WeaponDetail />} />
          <Route path="/strategy/:key" element={<StrategyView />} />
          <Route path="/deposition/:id" element={<DepositionRoom />} />
        </Routes>
      </div>
    </Router>
  )
}
