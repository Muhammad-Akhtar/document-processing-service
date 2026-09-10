type Props = {
  documentId: string | null
  contentType: string | null
  filename: string | null
  previewHref: string | null
}

export function PreviewPane({ documentId, contentType, filename, previewHref }: Props) {
  if (!documentId || !previewHref || !contentType) {
    return (
      <div className="preview empty">
        <p>Select or upload a document to preview.</p>
      </div>
    )
  }

  const isPdf = contentType.includes('pdf')
  const isHtml = contentType.includes('html')

  return (
    <div className="preview">
      <header className="preview-header">
        <h2>{filename ?? 'Preview'}</h2>
        <span className="muted">{contentType}</span>
      </header>
      {isPdf ? (
        <iframe title="PDF preview" className="preview-frame" src={previewHref} />
      ) : isHtml ? (
        <iframe
          title="HTML preview"
          className="preview-frame"
          src={previewHref}
          sandbox="allow-same-origin"
        />
      ) : (
        <p className="muted">Preview is not available for this content type.</p>
      )}
    </div>
  )
}
