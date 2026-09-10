import { useEffect, useMemo, useState } from 'react'
import { ActionBar } from '../components/ActionBar'
import { DropZone } from '../components/DropZone'
import { ErrorBanner } from '../components/ErrorBanner'
import { HistoryList } from '../components/HistoryList'
import { PreviewPane } from '../components/PreviewPane'
import { ProgressBar } from '../components/ProgressBar'
import { TopBar } from '../components/TopBar'
import {
  convertDocument,
  deleteDocument,
  downloadUrl,
  previewUrl,
  uploadDocument,
} from '../api/documents'
import { ApiError } from '../api/client'
import {
  detectSourceKind,
  isAllowedUpload,
  targetFormatFor,
} from '../lib/formats'
import {
  loadHistory,
  removeHistoryItem,
  saveHistory,
  upsertHistoryItem,
} from '../lib/history'
import type { HistoryItem } from '../types/api'

type SelectedDoc = {
  id: string
  filename: string
  contentType: string
  size: number
}

export function WorkspacePage() {
  const [history, setHistory] = useState<HistoryItem[]>(() => loadHistory())
  const [selected, setSelected] = useState<SelectedDoc | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [converting, setConverting] = useState(false)

  useEffect(() => {
    saveHistory(history)
  }, [history])

  const sourceKind = useMemo(
    () =>
      selected
        ? detectSourceKind(selected.filename, selected.contentType)
        : 'unknown',
    [selected],
  )
  const target = targetFormatFor(sourceKind)
  const convertLabel =
    target === 'pdf' ? 'Convert to PDF' : target === 'html' ? 'Convert to HTML' : 'Convert'

  function remember(item: HistoryItem) {
    setHistory((prev) => upsertHistoryItem(prev, item))
  }

  async function handleFile(file: File) {
    setError(null)
    const check = isAllowedUpload(file.name, file.size)
    if (!check.ok) {
      setError(check.reason)
      return
    }

    setUploading(true)
    setUploadProgress(0)
    try {
      const uploaded = await uploadDocument(file, (ratio) => setUploadProgress(ratio))
      const doc: SelectedDoc = {
        id: uploaded.document_id,
        filename: uploaded.filename,
        contentType: uploaded.content_type,
        size: uploaded.size,
      }
      setSelected(doc)
      remember({
        id: doc.id,
        filename: doc.filename,
        contentType: doc.contentType,
        size: doc.size,
        status: 'uploaded',
        createdAt: new Date().toISOString(),
      })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }

  async function handleConvert() {
    if (!selected || !target) return
    setError(null)
    setConverting(true)
    try {
      const result = await convertDocument(selected.id, target)
      const doc: SelectedDoc = {
        id: result.output_document_id,
        filename: result.filename,
        contentType: result.content_type,
        size: result.size,
      }
      setSelected(doc)
      remember({
        id: doc.id,
        filename: doc.filename,
        contentType: doc.contentType,
        size: doc.size,
        status: 'converted',
        createdAt: new Date().toISOString(),
        sourceDocumentId: result.source_document_id,
        targetFormat: result.target_format,
      })
      if (result.warnings?.length) {
        setError(result.warnings.join(' '))
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Conversion failed')
      if (selected) {
        remember({
          id: selected.id,
          filename: selected.filename,
          contentType: selected.contentType,
          size: selected.size,
          status: 'failed',
          createdAt: new Date().toISOString(),
        })
      }
    } finally {
      setConverting(false)
    }
  }

  function handleDownload() {
    if (!selected) return
    window.open(downloadUrl(selected.id), '_blank', 'noopener,noreferrer')
  }

  async function handleDelete() {
    if (!selected) return
    if (!window.confirm(`Delete “${selected.filename}”?`)) return
    setError(null)
    try {
      await deleteDocument(selected.id)
      setHistory((prev) => removeHistoryItem(prev, selected.id))
      setSelected(null)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Delete failed')
    }
  }

  function handleSelectHistory(item: HistoryItem) {
    setSelected({
      id: item.id,
      filename: item.filename,
      contentType: item.contentType,
      size: item.size,
    })
    setError(null)
  }

  return (
    <div className="app-shell">
      <TopBar />
      <ErrorBanner message={error} onDismiss={() => setError(null)} />

      <main className="workspace">
        <section className="panel upload-panel">
          <h2>Upload</h2>
          <DropZone disabled={uploading || converting} onFile={handleFile} />
          {uploading ? <ProgressBar value={uploadProgress} label="Upload progress" /> : null}
          <ActionBar
            canConvert={Boolean(selected && target)}
            convertLabel={convertLabel}
            converting={converting}
            canDownload={Boolean(selected)}
            canDelete={Boolean(selected)}
            onConvert={handleConvert}
            onDownload={handleDownload}
            onDelete={handleDelete}
          />
        </section>

        <section className="panel preview-panel">
          <PreviewPane
            documentId={selected?.id ?? null}
            contentType={selected?.contentType ?? null}
            filename={selected?.filename ?? null}
            previewHref={selected ? previewUrl(selected.id) : null}
          />
        </section>

        <aside className="panel history-panel">
          <h2>History</h2>
          <HistoryList
            items={history}
            selectedId={selected?.id ?? null}
            onSelect={handleSelectHistory}
          />
        </aside>
      </main>
    </div>
  )
}
