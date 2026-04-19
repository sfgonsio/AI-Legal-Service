export default function CaseStrengthMeter({ strength = 0, label = 'Case Strength' }) {
  const percentage = Math.min(100, Math.max(0, strength))
  const getColor = (value) => {
    if (value < 40) return 'bg-red-600'
    if (value < 70) return 'bg-amber-500'
    return 'bg-emerald-500'
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-medium text-slate-300">{label}</span>
        <span className="text-sm font-mono text-slate-400">{percentage.toFixed(0)}%</span>
      </div>
      <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full ${getColor(percentage)} transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
