import { useState, useEffect } from 'react'

export default function AttorneyNotes({ initialValue = '', onSave }) {
  const [value, setValue] = useState(initialValue)
  const [isEditing, setIsEditing] = useState(false)
  const [isSaved, setIsSaved] = useState(true)

  useEffect(() => {
    setValue(initialValue)
    setIsSaved(true)
  }, [initialValue])

  const handleChange = (e) => {
    setValue(e.target.value)
    setIsSaved(false)
  }

  const handleSave = async () => {
    if (onSave) {
      await onSave(value)
    }
    setIsSaved(true)
    setIsEditing(false)
  }

  const handleRevert = () => {
    setValue(initialValue)
    setIsSaved(true)
    setIsEditing(false)
  }

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <label className="text-sm font-medium text-slate-300">Attorney Notes</label>
        {!isEditing && (
          <button
            onClick={() => setIsEditing(true)}
            className="text-xs px-2 py-1 bg-slate-700 hover:bg-slate-600 rounded transition-colors"
          >
            Edit
          </button>
        )}
      </div>

      {isEditing ? (
        <div className="space-y-2">
          <textarea
            value={value}
            onChange={handleChange}
            className="w-full bg-slate-800 border border-slate-600 rounded p-3 text-sm text-slate-100 focus:outline-none focus:border-blue-500 resize-none"
            rows={4}
          />
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={isSaved}
              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:text-slate-500 text-white text-sm rounded transition-colors"
            >
              Save
            </button>
            <button
              onClick={handleRevert}
              className="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-sm rounded transition-colors"
            >
              Revert
            </button>
          </div>
        </div>
      ) : (
        <div className="bg-slate-800/50 rounded p-3 text-sm text-slate-300 min-h-20">
          {value || <span className="text-slate-500 italic">No notes yet...</span>}
        </div>
      )}
    </div>
  )
}
