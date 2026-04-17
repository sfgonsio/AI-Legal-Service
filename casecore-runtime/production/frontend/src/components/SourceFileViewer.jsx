import { useState } from 'react'

export default function SourceFileViewer({ document }) {
  const [expanded, setExpanded] = useState(false)

  if (!document) return null

  const getFileIcon = (fileType) => {
    const icons = {
      'pdf': '📄',
      'email': '📧',
      'text': '📝',
      'image': '🖼',
      'unknown': '📎'
    }
    return icons[fileType] || icons.unknown
  }

  return (
    <div className="card">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left hover:text-blue-400 transition-colors flex items-start justify-between"
      >
        <div className="flex items-start gap-3 flex-1">
          <span className="text-xl">{getFileIcon(document.file_type)}</span>
          <div className="flex-1">
            <div className="font-medium text-slate-200">{document.filename}</div>
            <div className="text-xs text-slate-500 mt-1">
              {document.char_count} chars • {document.file_type}
            </div>
          </div>
        </div>
        <span className="text-slate-400">{expanded ? '−' : '+'}</span>
      </button>

      {expanded && (
        <div className="mt-4 space-y-3 border-t border-slate-700 pt-4 text-sm">
          <div>
            <div className="text-slate-400 font-medium mb-2">Content Preview:</div>
            <div className="bg-slate-900 rounded p-3 text-slate-300 max-h-48 overflow-y-auto text-xs font-mono">
              {document.text_content?.slice(0, 500)}
              {document.text_content?.length > 500 && '...'}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <div className="text-slate-400 font-medium mb-1">Hash:</div>
              <div className="text-slate-500 font-mono text-xs truncate">
                {document.sha256_hash?.slice(0, 16)}...
              </div>
            </div>
            <div>
              <div className="text-slate-400 font-medium mb-1">Uploaded:</div>
              <div className="text-slate-500 text-xs">
                {new Date(document.created_at).toLocaleDateString()}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
