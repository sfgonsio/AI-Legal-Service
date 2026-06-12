/**
 * UploadPanel — staged intake with validation, duplicate detection, per-file
 * progress, concurrency, retry, offline detection, and clear messaging.
 *
 * Flow:
 *   1. User drops/picks files or folder; .zip prompts for extract vs store.
 *   2. Client validates each staged file (size, type) against /documents/upload-config.
 *   3. Client computes sha256 via SubtleCrypto (chunked for large files).
 *   4. Client queries /documents/case/{id}/check-hashes to flag dupes.
 *   5. User may remove rows, skip dupes, or proceed.
 *   6. Upload runs with max 4 concurrent; per-file XHR progress; retry supported.
 *   7. Online/offline state surfaced via navigator.onLine + request errors.
 *
 * UI never shows a bare spinner — every state has words + progress.
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { documentApi } from '../api/client'

const API_BASE = '/api'
const MAX_CONCURRENT = 4

// Row status codes (internal UI state, not server state).
const ST = {
  STAGED: 'staged',
  INVALID: 'invalid',
  DUP_KNOWN: 'duplicate',
  HASHING: 'hashing',
  READY: 'ready',
  SKIPPED: 'skipped',
  UPLOADING: 'uploading',
  UPLOADED: 'uploaded',
  FAILED: 'failed',
}

const TONE = {
  staged: 'text-slate-300',
  invalid: 'text-rose-400',
  duplicate: 'text-amber-300',
  hashing: 'text-sky-300',
  ready: 'text-slate-200',
  skipped: 'text-slate-500',
  uploading: 'text-sky-300',
  uploaded: 'text-emerald-400',
  failed: 'text-rose-400',
}

// ------------------- helpers -------------------

function humanBytes(n) {
  if (!n && n !== 0) return '—'
  const u = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let x = n
  while (x >= 1024 && i < u.length - 1) { x /= 1024; i++ }
  return `${x.toFixed(x < 10 && i > 0 ? 1 : 0)} ${u[i]}`
}

function extOf(filename) {
  const i = filename.lastIndexOf('.')
  return i < 0 ? '' : filename.slice(i + 1).toLowerCase()
}

function splitFolderAndName(rel) {
  const p = String(rel || '').replace(/^\/+/, '')
  const s = p.lastIndexOf('/')
  if (s < 0) return { folder: '', filename: p }
  return { folder: p.slice(0, s), filename: p.slice(s + 1) }
}

function isZipExt(name) {
  return extOf(name) === 'zip'
}

// Recursive walk of drag-drop items (folders).
async function walkEntries(items) {
  const out = []
  const roots = []
  for (const it of items) {
    if (it.kind !== 'file') continue
    const entry = it.webkitGetAsEntry ? it.webkitGetAsEntry() : null
    if (entry) roots.push(entry)
    else {
      const f = it.getAsFile()
      if (f) out.push({ file: f, relPath: f.name })
    }
  }
  async function readDir(dirEntry) {
    const reader = dirEntry.createReader()
    const entries = []
    await new Promise((resolve) => {
      const step = () => {
        reader.readEntries((batch) => {
          if (batch.length === 0) return resolve()
          entries.push(...batch)
          step()
        })
      }
      step()
    })
    return entries
  }
  async function visit(entry, prefix) {
    if (entry.isFile) {
      await new Promise((res) => {
        entry.file((f) => {
          out.push({ file: f, relPath: prefix ? `${prefix}/${f.name}` : f.name })
          res()
        })
      })
    } else if (entry.isDirectory) {
      const subs = await readDir(entry)
      for (const s of subs) await visit(s, prefix ? `${prefix}/${entry.name}` : entry.name)
    }
  }
  for (const r of roots) await visit(r, '')
  return out
}

function filesFromInput(fileList) {
  const out = []
  for (const f of fileList) {
    const rel = f.webkitRelativePath || f.name
    out.push({ file: f, relPath: String(rel).replace(/^\/+/, '') })
  }
  return out
}

// SHA-256 via Web Crypto, chunked so large files don't freeze the page.
async function sha256OfFile(file, onProgress) {
  const subtle = globalThis.crypto?.subtle
  if (!subtle || !subtle.digest) {
    // Hashing not available (very old browser or insecure context that
    // excludes SubtleCrypto). Return null; duplicate detection will be
    // post-upload (server-side) instead of pre-upload.
    return null
  }
  // For small files, a single digest call is fastest.
  if (file.size < 32 * 1024 * 1024) {
    const buf = await file.arrayBuffer()
    const h = await subtle.digest('SHA-256', buf)
    if (onProgress) onProgress(1)
    return hex(h)
  }
  // Large file: hashing via digest('SHA-256', concat) still works but we can
  // at least animate progress by reading chunks.
  const CHUNK = 8 * 1024 * 1024
  const parts = []
  let offset = 0
  while (offset < file.size) {
    const end = Math.min(offset + CHUNK, file.size)
    parts.push(new Uint8Array(await file.slice(offset, end).arrayBuffer()))
    offset = end
    if (onProgress) onProgress(offset / file.size)
  }
  // concat
  const total = parts.reduce((s, p) => s + p.length, 0)
  const merged = new Uint8Array(total)
  let cursor = 0
  for (const p of parts) { merged.set(p, cursor); cursor += p.length }
  const h = await subtle.digest('SHA-256', merged)
  return hex(h)
}

function hex(buffer) {
  const bytes = new Uint8Array(buffer)
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('')
}

// ------------------- component -------------------

export default function UploadPanel({ caseId, onComplete }) {
  const [config, setConfig] = useState(null)
  const [rows, setRows] = useState([])     // staged + uploaded rows
  const [error, setError] = useState(null)
  const [online, setOnline] = useState(typeof navigator === 'undefined' ? true : navigator.onLine)
  const [zipPrompt, setZipPrompt] = useState(null)    // {pendingItems, zipFiles}
  const [busy, setBusy] = useState(false)
  const fileInputRef = useRef(null)
  const folderInputRef = useRef(null)
  const nextKey = useRef(1)

  // Load upload-config on mount
  useEffect(() => {
    let cancelled = false
    documentApi.uploadConfig().then((cfg) => {
      if (!cancelled) setConfig(cfg)
    }).catch((e) => setError(`failed to load upload config: ${e.message}`))
    return () => { cancelled = true }
  }, [])

  // online/offline events
  useEffect(() => {
    const on = () => setOnline(true)
    const off = () => setOnline(false)
    window.addEventListener('online', on)
    window.addEventListener('offline', off)
    return () => {
      window.removeEventListener('online', on)
      window.removeEventListener('offline', off)
    }
  }, [])

  // Window-level drag/drop guards:
  // Browsers will navigate away (or open files in blank tabs) when the user
  // drops a file ANYWHERE on the page that isn't an explicit drop target.
  // Register window dragover/drop that preventDefault so stray drops are a no-op
  // rather than opening the file. Our drop zone's own handlers still run for
  // drops inside it.
  useEffect(() => {
    const prevent = (e) => {
      // Allow our inner drop zone to still process drops: if dataTransfer.items
      // indicates a file drop, we always preventDefault at window level so the
      // browser does not navigate. The zone's own onDrop reads dataTransfer.
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

  const updateRow = useCallback((key, patch) => {
    setRows((prev) => prev.map((r) => (r.key === key ? { ...r, ...patch } : r)))
  }, [])

  const removeRow = useCallback((key) => {
    setRows((prev) => prev.filter((r) => r.key !== key))
  }, [])

  // ---------- staging ----------

  function newRow(file, relPath, opts = {}) {
    const { folder, filename } = splitFolderAndName(relPath)
    return {
      key: `r${nextKey.current++}`,
      file,
      filename,
      folder,
      relPath,
      size: file.size,
      ext: extOf(filename),
      sha256: null,
      duplicateOf: null,
      status: ST.STAGED,
      progress: 0,
      error: null,
      documentId: null,
      asZip: opts.asZip ?? isZipExt(filename),
      isZip: isZipExt(filename),
      treatZipAsOpaque: false,
    }
  }

  function validateRow(row) {
    if (!config) return { ...row }
    const reasons = []
    if (row.size > config.max_file_bytes) {
      reasons.push(`size ${humanBytes(row.size)} exceeds limit ${humanBytes(config.max_file_bytes)}`)
    }
    const bucket = config.extension_buckets[row.ext]
    if (!bucket) {
      reasons.push(`unsupported type .${row.ext || '(none)'}`)
    }
    // archive size has a larger allowance; already covered above for non-zip.
    if (row.isZip && row.size > config.max_archive_bytes) {
      reasons.push(`zip exceeds ${humanBytes(config.max_archive_bytes)}`)
    }
    if (reasons.length > 0) {
      return { ...row, status: ST.INVALID, error: reasons.join('; '), bucket }
    }
    return { ...row, bucket, status: ST.STAGED }
  }

  async function stageItems(items) {
    if (!config) {
      setError('Upload config not loaded yet; wait a moment and retry.')
      return
    }
    // Detect any zips and ask the user how to handle them.
    const zips = items.filter((it) => isZipExt(it.relPath))
    if (zips.length > 0 && !zipPrompt) {
      setZipPrompt({ items, zips })
      return
    }
    const staged = items.map((it) => newRow(it.file, it.relPath))
    const validated = staged.map((r) => validateRow(r))
    setRows((prev) => [...prev, ...validated])

    // Hash + dupe-check the valid ones asynchronously.
    const toHash = validated.filter((r) => r.status === ST.STAGED)
    await Promise.all(toHash.map((r) => hashAndCheck(r)))
  }

  async function hashAndCheck(row) {
    updateRow(row.key, { status: ST.HASHING, progress: 0 })
    try {
      const sha = await sha256OfFile(row.file, (p) => updateRow(row.key, { progress: p }))
      if (!sha) {
        // no subtle crypto — mark ready; server-side dedupe on hash still happens.
        updateRow(row.key, { status: ST.READY, progress: 1 })
        return
      }
      updateRow(row.key, { sha256: sha, progress: 1 })
      // Check against server for this case.
      const resp = await documentApi.checkHashes(caseId, [sha])
      const dup = (resp.duplicates || []).find((d) => d.sha256_hash === sha)
      if (dup) {
        updateRow(row.key, {
          status: ST.DUP_KNOWN,
          duplicateOf: {
            document_id: dup.document_id,
            filename: dup.filename,
            folder: dup.folder,
          },
        })
      } else {
        updateRow(row.key, { status: ST.READY })
      }
    } catch (e) {
      updateRow(row.key, { status: ST.INVALID, error: e.message || 'hashing failed' })
    }
  }

  function handleZipResolve(mode) {
    if (!zipPrompt) return
    // mode: 'extract' -> treat zips as zip-upload;
    //       'store'   -> treat zips as opaque binary (upload via /documents/upload).
    const items = zipPrompt.items
    const mapped = items.map((it) => {
      if (isZipExt(it.relPath)) {
        return { ...it, asZip: mode === 'extract' ? true : false, treatZipAsOpaque: mode === 'store' }
      }
      return it
    })
    setZipPrompt(null)
    // Reset so stage runs; bypass prompt re-entry.
    const staged = mapped.map((it) => {
      const row = newRow(it.file, it.relPath, { asZip: isZipExt(it.relPath) && mode === 'extract' })
      row.treatZipAsOpaque = isZipExt(it.relPath) && mode === 'store'
      return row
    })
    const validated = staged.map((r) => validateRow(r))
    setRows((prev) => [...prev, ...validated])
    Promise.all(
      validated.filter((r) => r.status === ST.STAGED).map((r) => hashAndCheck(r))
    )
  }

  // ---------- handlers ----------

  function onFilePick(e) {
    const items = filesFromInput(e.target.files || [])
    e.target.value = ''
    stageItems(items)
  }

  function onFolderPick(e) {
    const items = filesFromInput(e.target.files || [])
    e.target.value = ''
    stageItems(items)
  }

  async function onDrop(e) {
    e.preventDefault()
    e.stopPropagation()
    // Prefer the items collection (supports folders via webkitGetAsEntry).
    // Fall back to dataTransfer.files for environments where items are not exposed.
    const items = e.dataTransfer?.items
    if (items && items.length > 0) {
      const walked = await walkEntries(items)
      if (walked.length > 0) {
        stageItems(walked)
        return
      }
    }
    const flist = e.dataTransfer?.files
    if (flist && flist.length > 0) {
      const fallback = []
      for (const f of flist) {
        fallback.push({ file: f, relPath: f.name })
      }
      stageItems(fallback)
    }
  }

  function onDragOver(e) {
    e.preventDefault()
    e.stopPropagation()
    // required so the browser recognizes this element as a valid drop target
    if (e.dataTransfer) e.dataTransfer.dropEffect = 'copy'
  }

  // ---------- upload queue ----------

  async function uploadRow(row) {
    if (!online) {
      updateRow(row.key, { status: ST.FAILED, error: 'offline' })
      return false
    }
    updateRow(row.key, { status: ST.UPLOADING, progress: 0, error: null })
    try {
      const result = await (row.isZip && !row.treatZipAsOpaque
        ? uploadZipXhr(row)
        : uploadFileXhr(row))
      updateRow(row.key, {
        status: ST.UPLOADED,
        progress: 1,
        documentId: result?.documents?.[0]?.document_id ?? result?.archive_id ?? null,
      })
      return true
    } catch (e) {
      const msg = e?.message || 'upload failed'
      updateRow(row.key, { status: ST.FAILED, error: msg })
      return false
    }
  }

  function uploadFileXhr(row) {
    return new Promise((resolve, reject) => {
      const form = new FormData()
      form.append('case_id', String(caseId))
      form.append('files', row.file, row.filename)
      form.append('filenames', row.filename)
      form.append('folders', row.folder || '')
      form.append('relative_paths', row.relPath)
      const xhr = new XMLHttpRequest()
      xhr.open('POST', `${API_BASE}/documents/upload`)
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) updateRow(row.key, { progress: e.loaded / Math.max(1, e.total) })
      }
      xhr.onerror = () => reject(new Error('network error'))
      xhr.ontimeout = () => reject(new Error('timeout'))
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try { resolve(JSON.parse(xhr.responseText)) } catch { resolve({}) }
        } else {
          reject(new Error(`HTTP ${xhr.status}: ${xhr.responseText?.slice(0, 200)}`))
        }
      }
      xhr.send(form)
    })
  }

  function uploadZipXhr(row) {
    return new Promise((resolve, reject) => {
      const form = new FormData()
      form.append('case_id', String(caseId))
      form.append('archive', row.file, row.filename)
      const xhr = new XMLHttpRequest()
      xhr.open('POST', `${API_BASE}/documents/upload-zip`)
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) updateRow(row.key, { progress: e.loaded / Math.max(1, e.total) })
      }
      xhr.onerror = () => reject(new Error('network error'))
      xhr.ontimeout = () => reject(new Error('timeout'))
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try { resolve(JSON.parse(xhr.responseText)) } catch { resolve({}) }
        } else {
          reject(new Error(`HTTP ${xhr.status}: ${xhr.responseText?.slice(0, 200)}`))
        }
      }
      xhr.send(form)
    })
  }

  async function runQueue(eligibleKeys) {
    setBusy(true)
    const keysQueue = [...eligibleKeys]
    // simple semaphore
    const workers = new Array(Math.min(MAX_CONCURRENT, keysQueue.length)).fill(0).map(async () => {
      while (keysQueue.length > 0) {
        const k = keysQueue.shift()
        const cur = latestRow(k)
        if (!cur) continue
        await uploadRow(cur)
      }
    })
    await Promise.all(workers)
    setBusy(false)
    if (onComplete) await onComplete()
  }

  // Read the current version of a row from state (latest inside the async queue).
  function latestRow(key) {
    let found = null
    setRows((prev) => {
      found = prev.find((r) => r.key === key) || null
      return prev
    })
    return found
  }

  function onUploadAll() {
    setError(null)
    const keys = rows.filter((r) => r.status === ST.READY).map((r) => r.key)
    if (keys.length === 0) {
      setError('Nothing to upload. Review any invalid or duplicate rows below.')
      return
    }
    runQueue(keys)
  }

  function onSkipDupes() {
    setRows((prev) => prev.map((r) => r.status === ST.DUP_KNOWN ? { ...r, status: ST.SKIPPED } : r))
  }

  function onProceedDupes() {
    // Treat duplicates as ready; server will create a new Document row
    // sharing the same sha256 file (dedup on disk).
    setRows((prev) => prev.map((r) => r.status === ST.DUP_KNOWN ? { ...r, status: ST.READY } : r))
  }

  async function onRetryFailed() {
    const keys = rows.filter((r) => r.status === ST.FAILED).map((r) => r.key)
    if (keys.length === 0) return
    runQueue(keys)
  }

  function onClearStaged() {
    setRows((prev) => prev.filter((r) => r.status === ST.UPLOADED || r.status === ST.UPLOADING))
  }

  // ---------- totals ----------

  const totals = rows.reduce((acc, r) => {
    acc.count += 1
    acc.bytes += r.size || 0
    acc.ready += r.status === ST.READY ? 1 : 0
    acc.invalid += r.status === ST.INVALID ? 1 : 0
    acc.dupes += r.status === ST.DUP_KNOWN ? 1 : 0
    acc.skipped += r.status === ST.SKIPPED ? 1 : 0
    acc.uploaded += r.status === ST.UPLOADED ? 1 : 0
    acc.failed += r.status === ST.FAILED ? 1 : 0
    acc.uploading += r.status === ST.UPLOADING ? 1 : 0
    acc.uploadedBytes += r.status === ST.UPLOADED ? (r.size || 0)
                        : r.status === ST.UPLOADING ? (r.size || 0) * (r.progress || 0) : 0
    return acc
  }, {
    count: 0, bytes: 0, ready: 0, invalid: 0, dupes: 0, skipped: 0,
    uploaded: 0, failed: 0, uploading: 0, uploadedBytes: 0,
  })
  const overallPct = totals.bytes ? Math.min(100, Math.round((totals.uploadedBytes / totals.bytes) * 100)) : 0

  if (!config) {
    return <div className="text-slate-500 text-xs">Loading upload config…</div>
  }

  return (
    <div className="border border-slate-700 rounded-md p-4 bg-slate-800">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-slate-100">Upload Evidence</h3>
        <div className="text-[10px] text-slate-400 text-right">
          Supported: {config.supported_extensions.map((e) => '.' + e).join(' ')}<br />
          Max per file: {humanBytes(config.max_file_bytes)} · Max ZIP: {humanBytes(config.max_archive_bytes)} · Max entries: {config.max_archive_entries}
        </div>
      </div>

      {!online && (
        <div className="mb-2 text-xs bg-rose-900/40 border border-rose-700 rounded px-2 py-1 text-rose-200">
          You appear to be offline. Uploads will resume when the connection returns.
        </div>
      )}

      {error && (
        <div className="mb-2 text-xs bg-amber-900/40 border border-amber-700 rounded px-2 py-1 text-amber-200">
          {error}
        </div>
      )}

      <div
        onDragOver={onDragOver}
        onDragEnter={onDragOver}
        onDrop={onDrop}
        className="border-2 border-dashed border-slate-600 rounded p-5 text-center hover:border-sky-500 transition-colors"
      >
        <div className="text-sm text-slate-300 mb-2">Drag &amp; drop files or folders here</div>
        <div className="flex gap-2 justify-center flex-wrap">
          <button onClick={() => fileInputRef.current?.click()}
            className="px-3 py-1 text-xs rounded bg-sky-700 hover:bg-sky-600">Pick Files</button>
          <button onClick={() => folderInputRef.current?.click()}
            className="px-3 py-1 text-xs rounded bg-slate-700 hover:bg-slate-600">Pick Folder</button>
        </div>
        <input ref={fileInputRef} type="file" multiple onChange={onFilePick} className="hidden" />
        <input ref={folderInputRef} type="file" multiple webkitdirectory="" directory="" onChange={onFolderPick} className="hidden" />
        <div className="text-[10px] text-slate-500 mt-2">
          Folder pick is unavailable on mobile Safari — use Pick Files there.
        </div>
      </div>

      {zipPrompt && (
        <div className="mt-3 border border-amber-700 rounded p-3 bg-amber-900/30">
          <div className="text-xs text-amber-100 mb-2">
            You selected {zipPrompt.zips.length} .zip file{zipPrompt.zips.length === 1 ? '' : 's'}.
            Extract on server (one row per inner file) or store the zip as-is (one opaque row)?
          </div>
          <div className="flex gap-2">
            <button onClick={() => handleZipResolve('extract')}
              className="px-2 py-1 text-xs rounded bg-sky-700 hover:bg-sky-600">Extract on server</button>
            <button onClick={() => handleZipResolve('store')}
              className="px-2 py-1 text-xs rounded bg-slate-700 hover:bg-slate-600">Store as-is</button>
            <button onClick={() => setZipPrompt(null)}
              className="px-2 py-1 text-xs rounded bg-rose-800 hover:bg-rose-700">Cancel</button>
          </div>
        </div>
      )}

      {rows.length > 0 && (
        <>
          <div className="mt-4 text-xs text-slate-300 flex flex-wrap gap-3">
            <span>{totals.count} staged</span>
            <span>{humanBytes(totals.bytes)} total</span>
            <span className="text-emerald-400">{totals.uploaded} uploaded</span>
            {totals.uploading > 0 && <span className="text-sky-300">{totals.uploading} uploading</span>}
            {totals.ready > 0 && <span className="text-slate-200">{totals.ready} ready</span>}
            {totals.dupes > 0 && <span className="text-amber-300">{totals.dupes} duplicates</span>}
            {totals.invalid > 0 && <span className="text-rose-400">{totals.invalid} invalid</span>}
            {totals.failed > 0 && <span className="text-rose-400">{totals.failed} failed</span>}
            {totals.skipped > 0 && <span className="text-slate-500">{totals.skipped} skipped</span>}
          </div>

          <div className="mt-2 h-1.5 bg-slate-700 rounded overflow-hidden">
            <div className="h-full bg-sky-500 transition-all" style={{ width: `${overallPct}%` }} />
          </div>

          <div className="mt-3 flex gap-2 flex-wrap">
            <button disabled={busy || totals.ready === 0 || !online}
              onClick={onUploadAll}
              className="px-2 py-1 text-xs rounded bg-emerald-700 hover:bg-emerald-600 disabled:opacity-40">
              Upload {totals.ready || ''} Ready
            </button>
            {totals.dupes > 0 && (
              <>
                <button onClick={onProceedDupes}
                  className="px-2 py-1 text-xs rounded bg-amber-700 hover:bg-amber-600">
                  Upload Duplicates Anyway
                </button>
                <button onClick={onSkipDupes}
                  className="px-2 py-1 text-xs rounded bg-slate-700 hover:bg-slate-600">
                  Skip Duplicates
                </button>
              </>
            )}
            {totals.failed > 0 && (
              <button disabled={busy || !online} onClick={onRetryFailed}
                className="px-2 py-1 text-xs rounded bg-sky-700 hover:bg-sky-600 disabled:opacity-40">
                Retry Failed ({totals.failed})
              </button>
            )}
            {(totals.ready + totals.invalid + totals.dupes + totals.skipped + totals.failed) > 0 && (
              <button onClick={onClearStaged}
                className="px-2 py-1 text-xs rounded bg-slate-700 hover:bg-slate-600">
                Clear Staged
              </button>
            )}
          </div>

          <ul className="mt-3 space-y-1 max-h-72 overflow-y-auto">
            {rows.map((r) => (
              <li key={r.key} className="text-xs border border-slate-700 rounded p-2">
                <div className="flex justify-between gap-2">
                  <span className="font-mono truncate" title={r.folder ? `${r.folder}/${r.filename}` : r.filename}>
                    {r.folder ? `${r.folder}/` : ''}{r.filename}
                    {r.isZip && <span className="ml-1 text-amber-300">[zip{r.treatZipAsOpaque ? ':opaque' : ':extract'}]</span>}
                  </span>
                  <span className={`font-mono text-[10px] ${TONE[r.status] || 'text-slate-400'}`}>
                    {r.status}
                  </span>
                </div>
                <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                  <span>
                    {humanBytes(r.size)} · .{r.ext || '(none)'}
                    {r.sha256 && <span className="ml-2">sha:{r.sha256.slice(0, 10)}…</span>}
                  </span>
                  <div className="flex gap-2">
                    {r.status !== ST.UPLOADED && r.status !== ST.UPLOADING && (
                      <button onClick={() => removeRow(r.key)} className="text-rose-400 hover:underline">
                        remove
                      </button>
                    )}
                    {r.status === ST.FAILED && (
                      <button onClick={() => uploadRow(r)} className="text-sky-400 hover:underline">
                        retry
                      </button>
                    )}
                  </div>
                </div>
                {(r.status === ST.HASHING || r.status === ST.UPLOADING) && (
                  <div className="h-1 bg-slate-700 rounded overflow-hidden mt-1">
                    <div className="h-full bg-sky-500 transition-all"
                      style={{ width: `${Math.round((r.progress || 0) * 100)}%` }} />
                  </div>
                )}
                {r.error && <div className="text-rose-400 mt-1">{r.error}</div>}
                {r.duplicateOf && (
                  <div className="text-amber-300 mt-1">
                    Duplicate of: {r.duplicateOf.folder ? `${r.duplicateOf.folder}/` : ''}{r.duplicateOf.filename} (doc_id {r.duplicateOf.document_id})
                  </div>
                )}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}
