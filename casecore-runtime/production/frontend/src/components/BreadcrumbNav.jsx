import { useNavigate } from 'react-router-dom'

export default function BreadcrumbNav({ navStack }) {
  const navigate = useNavigate()

  return (
    <nav className="flex items-center gap-2 text-sm text-slate-400 mb-6">
      {navStack.map((item, idx) => (
        <div key={idx} className="flex items-center gap-2">
          {idx > 0 && <span>/</span>}
          <button
            onClick={() => navigate(item.path)}
            className="hover:text-slate-200 transition-colors"
          >
            {item.label}
          </button>
        </div>
      ))}
    </nav>
  )
}
